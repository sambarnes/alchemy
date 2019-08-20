import hashlib
import pylxr
import sys
from factom import Factomd

import alchemy.consts as consts
import alchemy.grading.graders as graders
from alchemy.opr import OPR


def run(n_blocks: int = None):
    factomd = Factomd()
    lxr = pylxr.LXR()
    stock_grader = graders.StockGrader(lxr)
    custom_grader = graders.StraightDifficultyGrader(lxr)

    start_height = consts.START_HEIGHT
    prev_winners = ["" for _ in range(10)]
    height = start_height
    while True:
        # First pass, collect all sane OPRs in block
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

        # Run the two graders
        stock_prices, stock_winners, stock_top50 = stock_grader.grade_records(prev_winners, current_block_records)
        custom_prices, custom_winners, custom_top50 = custom_grader.grade_records(prev_winners, current_block_records)

        if stock_winners is not None:
            print(f"\nBlock {height}")

            # Aggregate stats
            stock_rewards = {}
            custom_rewards = {}
            for i in range(10):
                reward = consts.BLOCK_REWARDS.get(i, 0)

                stock_coinbase = stock_winners[i].coinbase_address
                stock_rewards[stock_coinbase] = stock_rewards.get(stock_coinbase, 0) + reward

                custom_coinbase = custom_winners[i].coinbase_address
                custom_rewards[custom_coinbase] = custom_rewards.get(custom_coinbase, 0) + reward

            # Output results
            print("Stock:")
            print(f"\tRates: {stock_prices}")
            print(f"\tRewards: {stock_rewards}")
            print(f"\tUnique coinbases: {len(stock_rewards.keys())}")

            print("Custom:")
            print(f"\tRates: {custom_prices}")
            print(f"\tRewards: {custom_rewards}")
            print(f"\tUnique coinbases: {len(custom_rewards.keys())}")

            # Make sure prev winners are the stock ones, so we can keep grading all other records on mainnet
            prev_winners = [record.entry_hash[:8].hex() for record in stock_winners[:10]]
        else:
            print(f"\nSkipped block {height}")

        height += 1
        if n_blocks is not None and n_blocks < height - start_height:
            return


if __name__ == "__main__":
    if len(sys.argv) == 2:
        run(int(sys.argv[1]))
    else:
        run()
