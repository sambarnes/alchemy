import factom
import json
import numpy as np
from factom import Factomd
from typing import Dict, List

import consts
import db


def run(factomd: Factomd, database: db.AlchemyDB, is_testnet: bool = False):
    height_last_parsed = database.get_factoid_head()
    print(f"Highest Factoid Block parsed: {height_last_parsed}")

    # Parse Factoid Blocks looking for matching FCT burn transactions
    height = height_last_parsed + 1
    expected_burn_address = consts.BurnAddresses.MAINNET.value if not is_testnet else consts.BurnAddresses.TESTNET.value
    all_account_deltas: Dict[bytes, Dict[str, float]] = {}
    network_ticker = "p" if not is_testnet else "t"
    default_deltas = {f"{network_ticker}{ticker}": 0 for ticker in consts.ALL_PEGGED_ASSETS}
    while True:
        try:
            factoid_block = factomd.factoid_block_by_height(height)["fblock"]
        except factom.exceptions.BlockNotFound:
            break
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
            this_account_deltas = all_account_deltas.get(address, default_deltas)
            this_account_deltas[f"{network_ticker}FCT"] += burn_amount
            all_account_deltas[address] = this_account_deltas

        height += 1

    database.put_factoid_head(height - 1)  # Last block was not found, use height-1\
    for address, deltas in all_account_deltas.items():
        database.update_balances(address, deltas)
