import hashlib
import pylxr
from factom import Factomd
from typing import List

import alchemy.consts as consts
import alchemy.grading.graders as graders
from alchemy.opr import OPR


def process_block(height: int, previous_winners: List[str], factomd: Factomd, lxr: pylxr.LXR, is_testnet: bool = False):
    """Grades all entries in the OPR chain at the given height"""
    current_block_records = []
    entries = factomd.entries_at_height(consts.OPR_CHAIN_ID, height, include_entry_context=True)
    for e in entries:
        entry_hash = bytes.fromhex(e["entryhash"])
        external_ids, content, timestamp = e["extids"], e["content"], e["timestamp"]
        record = OPR.from_entry(entry_hash, external_ids, content, timestamp)
        if record is None or record.height != height:
            continue  # Failed sanity check, throw it out
        # It's a valid OPR, compute its hash and append to current block OPRs
        record.opr_hash = hashlib.sha256(content).digest()
        current_block_records.append(record)

    # Pluggable grader below. Swap out the following line for a custom implementation for testing purposes.
    grader = graders.StockGrader(lxr)
    return grader.grade_records(previous_winners, current_block_records)
