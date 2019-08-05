import asyncio
import pylxr
import uvloop
from factom import Factomd

import alchemy.burning
import alchemy.grading
from alchemy.db import AlchemyDB


async def run_monitor(is_testnet: bool = False):
    monitor_queue = asyncio.Queue()

    producer_coro = monitor_producer(monitor_queue)
    consumer_coro = monitor_consumer(monitor_queue, is_testnet)
    await asyncio.gather(producer_coro, consumer_coro)


async def monitor_producer(q: asyncio.Queue):
    factomd = Factomd()
    height = 0
    while True:
        latest_block = factomd.heights()["directoryblockheight"]
        print(f"Current Factom block height: {latest_block}")
        if height < latest_block:
            height = latest_block
            await q.put(height)
            print("Dispatched tasks. Sleeping for 1 minute...\n")
            await asyncio.sleep(60)
        else:
            print("No new blocks found. Sleeping for 10 seconds...\n")
            await asyncio.sleep(10)


async def monitor_consumer(q: asyncio.Queue, is_testnet: bool = False):
    factomd = Factomd()
    lxr = pylxr.LXR(map_size_bits=30)
    database = AlchemyDB(is_testnet, create_if_missing=True)
    while True:
        msg = await q.get()
        alchemy.grading.run(factomd, lxr, database, is_testnet)
        alchemy.burning.find_new_burns(factomd, database, is_testnet)
        q.task_done()


def run(is_testnet: bool):
    """Main entry point for an alchemy node"""
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    monitor = loop.run_until_complete(run_monitor(is_testnet))
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        monitor.close()
        loop.run_until_complete(monitor.wait_closed())
