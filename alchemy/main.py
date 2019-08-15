import aiorpc
import asyncio
import factom
import pylxr
import uvloop
from collections import defaultdict
from colorama import Fore as color
from factom import Factomd
from factom_keys.fct import FactoidAddress

import alchemy.burning
import alchemy.consts as consts
import alchemy.csv_exporting
import alchemy.grading
import alchemy.transactions
import alchemy.rpc
from alchemy.db import AlchemyDB


async def run_protocol(database: AlchemyDB, is_testnet: bool = False):
    lxr = pylxr.LXR(map_size_bits=30)
    factomd = Factomd()
    while True:
        sync_head = database.get_sync_head()
        latest_block = factomd.heights()["directoryblockheight"]
        if latest_block == sync_head:
            await asyncio.sleep(15)
            continue
        for height in range(sync_head + 1, latest_block + 1):
            print(f"\nExecuting block {height}...")
            execute_block(height, factomd, lxr, database, is_testnet)
        print("\nDone. Waiting for next block...")


def execute_block(height: int, factomd: Factomd, lxr: pylxr.LXR, database: AlchemyDB, is_testnet: bool = False):
    # Initialize previous winners array
    previous_winners_full = database.get_highest_winners()
    previous_winners = (
        [entry_hash[:8].hex() for entry_hash in previous_winners_full]
        if len(previous_winners_full) != 0
        else ["" for _ in range(10)]
    )
    winners, top50 = alchemy.grading.run(height, previous_winners, factomd, lxr, is_testnet)
    if winners is not None:
        # Update winners in database. Calculate PNT reward deltas. Export winning prices to csv
        winning_entry_hashes = [record.entry_hash for record in winners[:10]]
        database.put_winners(height, winning_entry_hashes)
        database.put_winners_head(height)

        pnt_deltas = defaultdict(float)
        for i, record in enumerate(winners):
            pnt_deltas[record.coinbase_address] += consts.BLOCK_REWARDS.get(i, 0)

        # Graphing: write winning prices and the winning difficulty range to csv
        alchemy.csv_exporting.write_prices(winners[0])
        alchemy.csv_exporting.write_difficulty(top50[0], top50[-1])

        # Update PNT balances in database
        for address, delta in pnt_deltas.items():
            address_bytes = FactoidAddress(address_string=address).rcd_hash
            database.update_balances(address_bytes, {consts.PNT: delta})

        print(f"{color.GREEN}Graded OPR block {height} (winners: {previous_winners}){color.RESET}")
    else:
        print(f"{color.RED}Skipped OPR block {height} (<10 records passed grading){color.RESET}")

    print(f"Finished grading block {height}")

    # Burns
    try:
        burn_count, account_deltas = alchemy.burning.parse_factoid_block(height, factomd, is_testnet)
        for address, deltas in account_deltas.items():
            database.update_balances(address, deltas)
        print(f"Parsed factoid block {height} (burns found: {burn_count})")
    except factom.exceptions.BlockNotFound:
        pass

    database.put_sync_head(height)


def run(is_testnet: bool):
    """Main entry point for an alchemy node"""
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)

    database = AlchemyDB(is_testnet, create_if_missing=True)
    alchemy.rpc.register_database_functions(database)

    server_coro = asyncio.start_server(aiorpc.serve, "127.0.0.1", 6000, loop=loop)
    server = loop.run_until_complete(server_coro)
    try:
        loop.run_until_complete(run_protocol(database, is_testnet))
    except (KeyboardInterrupt, SystemExit):
        server.close()
        loop.run_until_complete(server.wait_closed())
