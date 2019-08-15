import numpy as np
from factom import Factomd
from typing import Dict

import alchemy.consts as consts
from alchemy.db import AlchemyDB
from alchemy.transactions.models import TransactionEntry


def process_block(height: int, rates: Dict[str, np.float64], factomd: Factomd, database: AlchemyDB):
    entries = factomd.entries_at_height(consts.TRANSACTIONS_CHAIN_ID, height, include_entry_context=True)
    for e in entries:
        tx_entry = TransactionEntry.from_entry(external_ids=e["extids"], content=e["content"])
        if tx_entry is None:
            print(f"Invalid transaction: {e}")
        else:
            print(f"Valid transaction: {tx_entry.get_deltas(rates)}")


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
