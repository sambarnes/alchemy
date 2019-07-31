import pylxr
from typing import List

import consts
from opr import OPR, AssetEstimates


def grade_entries(lxr: pylxr.LXR, previous_winners: List[bytes], entries: List[dict]):
    # First pass of OPR validation
    # Collect every sane entry, sorting by self reported difficulty as we go
    records_by_height = {}
    current_block_records = []
    height = 0
    for e in reversed(entries):
        if height != e["dbheight"]:
            if 10 <= len(current_block_records):
                current_block_records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
                records_by_height[height] = current_block_records
            current_block_records = []
            height = e["dbheight"]

        # If f it's a valid OPR, compute its hash and append to current block OPRs
        entry_hash = bytes.fromhex(e["entryhash"])
        external_ids, content = e["extids"], e["content"]
        record = OPR.from_entry(entry_hash, external_ids, content)
        if record is None:
            continue
        record.opr_hash = lxr.h(content)
        current_block_records.append(record)
    if 10 <= len(current_block_records):
        current_block_records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
        records_by_height[height] = current_block_records
        current_block_records = None  # Unset to discourage further use in the function

    # Grade block by block
    for height, records in records_by_height.items():
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
            continue  # Must have at least 10 valid submissions to grade them

        # TODO: opr.RemoveDuplicateSubmissions().
        #       Technically not needed, but should match reference implementation

        # Then calculate grade for each record in the top 50 and sort
        for i in range(len(valid_records) - 1, -1, -1):
            if i < 10:
                break
            averages = average_estimates(valid_records[:i])
            for j in range(i):
                valid_records[j].calculate_grade(averages)
            valid_records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
            valid_records.sort(key=lambda x: x.grade)

        # Set the previous winners
        winners = valid_records[:10]
        previous_winners = [o.entry_hash[:8].hex() for o in winners]
        records_by_height[height] = winners

    return records_by_height


def average_estimates(records: List[OPR]) -> AssetEstimates:
    """Computes the average answer for the price of each token reported"""
    averages: AssetEstimates = {k: 0 for k in consts.ALL_PEGGED_ASSETS}
    # Sum up all the prices
    for record in records:
        for k, v in record.asset_estimates.items():
            # Make sure no OPR has negative values for assets.  Simply treat all values as positive.
            averages[k] += abs(v)
    # Then divide the prices by the number of OraclePriceRecord records.  Two steps is actually faster
    # than doing everything in one loop (one divide for every asset rather than one divide
    # for every asset * number of OraclePriceRecords)  There is also a little bit of a precision advantage
    # with the two loops (fewer divisions usually does help with precision) but that isn't likely to be
    # interesting here.
    n_records = float(len(records))
    averages = {k: v / n_records for k, v in averages.items()}
    return averages
