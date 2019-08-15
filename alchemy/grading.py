import hashlib
import numpy as np
import pylxr
from factom import Factomd
from typing import List, Union

import alchemy.consts as consts
from alchemy.opr import OPR, AssetEstimates


def run(height: int, previous_winners: List[str], factomd: Factomd, lxr: pylxr.LXR, is_testnet: bool = False):
    """Grades all entries in the OPR chain at the given height"""
    current_block_records = []
    chain_id = consts.OPR_CHAIN_ID
    entries = factomd.read_chain(chain_id, from_height=height, include_entry_context=True)
    for e in entries:
        if height < e["dbheight"]:
            break
        # If it's a valid OPR, compute its hash and append to current block OPRs
        entry_hash = bytes.fromhex(e["entryhash"])
        external_ids, content, timestamp = e["extids"], e["content"], e["timestamp"]
        record = OPR.from_entry(entry_hash, external_ids, content, timestamp)
        if record is None or record.height != height:
            continue
        record.opr_hash = hashlib.sha256(content).digest()
        current_block_records.append(record)

    if 10 <= len(current_block_records):
        # We have enough sane records to grade. Sort by self reported difficulty do that now
        current_block_records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
        return grade_records(lxr, previous_winners, current_block_records)

    # Not enough sane records this block to even try grading
    return None, None


def grade_records(lxr: pylxr.LXR, previous_winners: List[str], records: List[OPR]):
    """Given a list of previous winners (first 8 bytes of entry hashes in hex), grade all records
    and return a list of the top 50, sorted by grade.
    """
    # First take top 50 by difficulty
    valid_records: List[OPR] = []
    for o in records:
        difficulty = lxr.h(o.opr_hash + o.nonce)[:8]
        if difficulty != o.self_reported_difficulty:
            print(
                f"Dishonest OPR difficulty: e_hash={o.entry_hash.hex()}, observed={difficulty.hex()}, reported={o.self_reported_difficulty.hex()}"
            )
            continue
        if o.prev_winners != previous_winners:
            continue
        valid_records.append(o)
        if 50 <= len(valid_records):
            break  # Found max number of honest submissions, go grade them

    if len(valid_records) < 10:
        return None, None  # Must have at least 10 valid submissions to grade them

    # TODO: opr.RemoveDuplicateSubmissions().
    #       Technically not needed, but should match reference implementation

    graded_records = valid_records
    # Then calculate grade for each record in the top 50 and sort
    for i in range(len(graded_records) - 1, -1, -1):
        if i < 10:
            break
        averages = average_estimates(graded_records[:i])
        for j in range(i):
            graded_records[j].grade = calculate_grade(graded_records[j].asset_estimates, averages)
        graded_records[:i] = sorted(graded_records[:i], key=lambda x: x.self_reported_difficulty, reverse=True)
        graded_records[:i] = sorted(graded_records[:i], key=lambda x: x.grade)

    return graded_records[:10], valid_records  # Return top 50 in graded order, top 10 are the winners


def average_estimates(records: List[OPR]) -> AssetEstimates:
    """Computes the average answer for the price of each token reported"""
    averages: AssetEstimates = {k: np.float64(0) for k in consts.ALL_ASSETS}
    # Sum up all the prices
    for record in records:
        for k, v in record.asset_estimates.items():
            # Make sure no OPR has negative values for assets.  Simply treat all values as positive.
            averages[k] += np.float64(abs(v))
    # Then divide the prices by the number of OraclePriceRecord records.  Two steps is actually faster
    # than doing everything in one loop (one divide for every asset rather than one divide
    # for every asset * number of OraclePriceRecords)  There is also a little bit of a precision advantage
    # with the two loops (fewer divisions usually does help with precision) but that isn't likely to be
    # interesting here.
    n_records = np.float64(len(records))
    averages = {k: v / n_records for k, v in averages.items()}
    return averages


def calculate_grade(record_estimates: AssetEstimates, averages: AssetEstimates) -> np.float64:
    """Given a map of price estimates and a second map of average estimates, calculate and return a grade
    where `grade = Σ(asset_difference^4)` over all assets in the set
    """
    grade = np.float64(0)
    for k, v in record_estimates.items():
        if averages[k] > 0:
            d = (v - averages[k]) / averages[k]
            grade += np.float64(d * d * d * d)
    return grade
