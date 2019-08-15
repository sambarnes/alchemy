from collections import defaultdict
from factom import Factomd
from typing import Dict

import alchemy.consts as consts


def process_block(height: int, factomd: Factomd, is_testnet: bool = False):
    """Parse all unseen Factoid Blocks looking for FCT burn transactions"""
    expected_burn_address = consts.BurnAddresses.MAINNET.value if not is_testnet else consts.BurnAddresses.TESTNET.value
    all_account_deltas: Dict[bytes, Dict[str:float]] = {}

    factoid_block = factomd.factoid_block_by_height(height)["fblock"]
    burn_count = 0
    transactions = factoid_block["transactions"]
    for tx in transactions:
        inputs = tx.get("inputs")
        outputs = tx.get("outputs")
        ec_outputs = tx.get("outecs")
        if len(inputs) != 1 or len(outputs) != 0 or len(ec_outputs) != 1:
            continue
        ec_address = ec_outputs[0].get("useraddress")
        if ec_address != expected_burn_address:
            continue

        # Successful burn, update the balance
        burn_amount = inputs[0].get("amount", 0)
        address = bytes.fromhex(inputs[0].get("address"))
        this_account_deltas = all_account_deltas.get(address, defaultdict(float))
        this_account_deltas[f"pFCT"] += burn_amount
        all_account_deltas[address] = this_account_deltas
        burn_count += 1

    return burn_count, all_account_deltas
