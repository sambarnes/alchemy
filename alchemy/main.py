import asyncio
import pylxr
import sys
from factom import Factomd, FactomWalletd

import alchemy.burning
import alchemy.grading
from alchemy.db import AlchemyDB


async def run(is_testnet: bool):
    """Main entry point for an alchemy node"""
    factomd = Factomd()
    lxr = pylxr.LXR(map_size_bits=30)
    database = AlchemyDB(is_testnet, create_if_missing=True)

    try:
        while True:
            latest_block = factomd.heights()["directoryblockheight"]
            print(f"Current Factom block height: {latest_block}")
            await asyncio.gather(
                alchemy.grading.run(factomd, lxr, database, is_testnet),
                alchemy.burning.find_new_burns(factomd, database, is_testnet),
            )
            print("\nDone. Sleeping for 1 minute...\n")
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
