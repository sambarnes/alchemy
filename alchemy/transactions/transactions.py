import numpy as np
from factom import Factomd, FactomWalletd
from factom_keys.ec import ECAddress
from typing import Dict

import alchemy.consts as consts
from alchemy.db import AlchemyDB
from alchemy.transactions.models import TransactionEntry


def run_parser(factomd: Factomd, database: AlchemyDB):
    height_last_parsed = database.get_transaction_head()
    print(f"\nHighest Transaction Block previously parsed: {height_last_parsed}")

    if height_last_parsed == -1:
        height_last_parsed += consts.START_HEIGHT

    # Run through all unseen entries
    current_height = height_last_parsed
    chain_id = consts.TRANSACTIONS_CHAIN_ID
    entries = factomd.read_chain(chain_id, from_height=height_last_parsed + 1, include_entry_context=True)
    for e in entries:
        if current_height != e["dbheight"]:
            current_height = e["dbheight"]
        tx_entry = TransactionEntry.from_entry(external_ids=e["extids"], content=e["content"])
        if tx_entry is None:
            print(f"Invalid transaction: {e}")
        else:
            print(f"Valid transaction: {tx_entry.get_deltas()}")

    # Update database checkpoint for Transaction chain
    if height_last_parsed < current_height:
        database.put_transaction_head(current_height)


def send(tx_entry: TransactionEntry, ec_address: ECAddress):
    factomd = Factomd(ec_address=ec_address.to_string())
    walletd = FactomWalletd()
    external_ids, content = tx_entry.sign()
    walletd.new_entry(factomd=factomd, chain_id=consts.TRANSACTIONS_CHAIN_ID, ext_ids=external_ids, content=content)


def execute_transaction_entry(database: AlchemyDB, tx_entry: TransactionEntry, rates: Dict[str, np.float64]):
    deltas = tx_entry.get_deltas(rates)
    for address, balance_deltas in deltas.items():
        working_balances = database.get_balances(address)
        for ticker, delta in balance_deltas.items():
            if ticker in working_balances:
                working_balances[ticker] += delta
            else:
                working_balances[ticker] = delta
        for balance in working_balances.values():
            if balance < 0:
                raise ValueError("Not enough funds to cover transaction")
    # All deltas check out, update the database
    for address, balance_deltas in deltas:
        database.update_balances(address, balance_deltas)
