import factom
import json
import numpy as np
import pylxr
from collections import defaultdict
from factom import Factomd
from factom_keys.fct import FactoidAddress
from typing import Iterable, List

import consts
import db
from opr import OPR, AssetEstimates


def run(factomd: Factomd, lxr: pylxr.LXR, database: db.AlchemyDB, is_testnet: bool = False):
    # Initialize previous winners array
    height_last_parsed = database.get_opr_head()
    print(f"\nHighest OPR Entry Block previously parsed: {height_last_parsed}")
    if height_last_parsed == -1:
        previous_winners = ["" for _ in range(10)]
    else:
        previous_winners_full = database.get_winners(height_last_parsed)
        previous_winners = [h[:8].hex() for h in previous_winners_full]

    # First pass of OPR validation
    # Collect all sane entries in each block, sorting by self reported difficulty as we go
    top50_by_height = {}
    current_block_records = []
    current_height = 0
    chain_id = consts.MAINNET_CHAIN_ID if not is_testnet else consts.TESTNET_CHAIN_ID
    entries = get_entries_from_height(factomd, chain_id, height_last_parsed + 1, True)
    for e in entries:
        if current_height != e["dbheight"]:
            if 10 <= len(current_block_records):
                # We have enough sane records to grade. Sort by self reported difficulty do that now
                current_block_records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
                top50 = grade_records(lxr, previous_winners, current_block_records)
                if top50 is not None:
                    previous_winners = [record.entry_hash[:8].hex() for record in top50[:10]]
                    top50_by_height[current_height] = top50
            current_block_records = []
            current_height = e["dbheight"]
            print(f"Grading records in block {current_height}...")

        # If it's a valid OPR, compute its hash and append to current block OPRs
        entry_hash = bytes.fromhex(e["entryhash"])
        external_ids, content = e["extids"], e["content"]
        record = OPR.from_entry(entry_hash, external_ids, content)
        if record is None:
            continue
        record.opr_hash = lxr.h(content)
        current_block_records.append(record)

    if 10 <= len(current_block_records):
        # (Repeat from above, just to flush out the last block of records.)
        # We have enough sane records to grade. Sort by self reported difficulty do that now
        current_block_records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
        top50 = grade_records(lxr, previous_winners, current_block_records)
        if top50 is not None:
            previous_winners = [record.entry_hash[:8].hex() for record in top50[:10]]
            top50_by_height[current_height] = top50

    print("Finished grading all unseen blocks")
    print("Updating database...")
    pnt_deltas = defaultdict(float)
    top_height_graded = None
    for height, records in top50_by_height.items():
        top_height_graded = height
        winners = [record.entry_hash for record in records[:10]]
        database.put_winners(height, winners)
        for i, record in enumerate(records):
            pnt_deltas[record.coinbase_address] += consts.BLOCK_REWARDS.get(i, 0)
    for address, delta in pnt_deltas.items():
        address_bytes = FactoidAddress(address_string=address).rcd_hash
        database.update_balances(address_bytes, {consts.PNT: delta})
    if top_height_graded is not None:
        database.put_opr_head(top_height_graded)


def get_entries_from_height(factomd: Factomd, chain_id: str, height: int, include_entry_context: bool = False):
    entry_blocks = []
    keymr = factomd.chain_head(chain_id)["chainhead"]
    while keymr != factom.client.NULL_BLOCK:
        block = factomd.entry_block(keymr)
        if block["header"]["dbheight"] < height:
            break
        entry_blocks.append(block)
        keymr = block["header"]["prevkeymr"]

    while len(entry_blocks) > 0:
        entry_block = entry_blocks.pop()
        for entry_pointer in reversed(entry_block["entrylist"]):
            entry = factomd.entry(entry_pointer["entryhash"])
            if include_entry_context:
                entry["entryhash"] = entry_pointer["entryhash"]
                entry["timestamp"] = entry_pointer["timestamp"]
                entry["dbheight"] = entry_block["header"]["dbheight"]
            yield entry


def grade_records(lxr: pylxr.LXR, previous_winners: List[str], records: List[OPR]):
    # First take top 50 by difficulty
    valid_records: List[OPR] = []
    for o in records:
        difficulty = lxr.h(o.opr_hash + o.nonce)[:8]
        if difficulty != o.self_reported_difficulty != difficulty:
            print(f"Dishonest OPR difficulty reported at entry: {o.entry_hash}")
            continue
        if o.prev_winners != previous_winners:
            continue
        valid_records.append(o)
        if 50 <= len(valid_records):
            break  # Found max number of honest submissions, go grade them

    if len(valid_records) < 10:
        return None  # Must have at least 10 valid submissions to grade them

    # TODO: opr.RemoveDuplicateSubmissions().
    #       Technically not needed, but should match reference implementation

    # Then calculate grade for each record in the top 50 and sort
    for i in range(len(valid_records) - 1, -1, -1):
        if i < 10:
            break
        averages = average_estimates(valid_records[:i])
        for j in range(i):
            valid_records[j].grade = calculate_grade(valid_records[j].asset_estimates, averages)
        valid_records[:i] = sorted(valid_records[:i], key=lambda x: x.self_reported_difficulty, reverse=True)
        valid_records[:i] = sorted(valid_records[:i], key=lambda x: x.grade)

    return valid_records  # Return top 50 in graded order, top 10 are the winners


def average_estimates(records: List[OPR]) -> AssetEstimates:
    """Computes the average answer for the price of each token reported"""
    averages: AssetEstimates = {k: np.float64(0) for k in consts.ALL_PEGGED_ASSETS}
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


def calculate_grade(record_estimates: AssetEstimates, averages: AssetEstimates):
    grade = np.float64(0)
    for k, v in record_estimates.items():
        if averages[k] > 0:
            # compute the difference from the average
            d = (v - averages[k]) / averages[k]
            # the grade is the sum of the square of the square of the differences
            grade += np.float64(d * d * d * d)
    return grade
