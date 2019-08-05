import factom
from collections import defaultdict
from factom import Factomd
from typing import Dict

import alchemy.consts as consts
from alchemy.db import AlchemyDB


def find_new_burns(factomd: Factomd, database: AlchemyDB, is_testnet: bool = False) -> None:
    """Parse all unseen Factoid Blocks looking for FCT burn transactions"""
    height_last_parsed = database.get_factoid_head()
    print(f"\nHighest Factoid Block previously parsed: {height_last_parsed}")

    height = height_last_parsed + 1
    expected_burn_address = consts.BurnAddresses.MAINNET.value if not is_testnet else consts.BurnAddresses.TESTNET.value
    all_account_deltas: Dict[bytes, Dict[str:float]] = {}
    network_ticker = "p" if not is_testnet else "t"
    while True:
        try:
            factoid_block = factomd.factoid_block_by_height(height)["fblock"]
        except factom.exceptions.BlockNotFound:
            break

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
            this_account_deltas[f"{network_ticker}FCT"] += burn_amount
            all_account_deltas[address] = this_account_deltas
            burn_count += 1

        print(f"Parsed factoid block {height} (burns found: {burn_count})")
        height += 1

    print("Updating FCT burn database...")
    database.put_factoid_head(height - 1)  # Last block was not found, use height-1\
    for address, deltas in all_account_deltas.items():
        database.update_balances(address, deltas)
