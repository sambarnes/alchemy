#!/usr/bin/env python3.7

import click
import factom.exceptions
import json
import pylxr
from factom import Factomd, FactomWalletd
from typing import Dict, List

import consts
from opr import OPR, average_estimates


HEADER = r"""
      o       
       o      
     ___      
     | |      
     | |      
     |o|             _      _                          
    .' '.       __ _| | ___| |__   ___ _ __ ___  _   _ 
   /  o  \     / _` | |/ __| '_ \ / _ \ '_ ` _ \| | | |
  :____o__:   | (_| | | (__| | | |  __/ | | | | | |_| |
  '._____.'    \__,_|_|\___|_| |_|\___|_| |_| |_|\__, |
                                                 |___/ 
"""


@click.group()
def main():
    pass


@main.command()
def run():
    """Main entry point for the node"""
    print(HEADER)


@main.command()
@click.argument("address", type=str)
@click.option("--testnet", is_flag=True)
def get_balances(address, testnet):
    """Get a list of all balances for the given address"""
    factomd = Factomd()
    try:
        fct_balance = factomd.factoid_balance(address).get("balance")
        fct_balance = fct_balance / consts.FACTOSHIS_PER_FCT
    except factom.exceptions.InvalidParams:
        print("Invalid Address")
        return
    network_ticker = "p" if not testnet else "t"
    balances = {f"{network_ticker}{ticker}": 0 for ticker in consts.ALL_PEGGED_ASSETS}
    balances["FCT"] = fct_balance
    balances[consts.PNT] = 0

    # Parse Factoid Blocks looking for matching FCT burn transactions
    height = consts.START_HEIGHT
    expected_burn_address = consts.BurnAddresses.MAINNET.value if not testnet else consts.BurnAddresses.TESTNET.value
    factoshis_burned = 0
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

            user_address = inputs[0].get("useraddress")
            if user_address != address:
                continue

            ec_address = ec_outputs[0].get("useraddress")
            if ec_address != expected_burn_address:
                continue

            # Successful burn, update the balance
            burn_amount = inputs[0].get("amount", 0)
            factoshis_burned += burn_amount
        height += 1
    balances[f"{network_ticker}FCT"] = factoshis_burned / consts.FACTOSHIS_PER_FCT

    # Parse OPR Chain for PNT rewards
    # Sort by self reported difficulty as we go
    entries = factomd.read_chain(consts.OPR_CHAIN_ID, include_entry_context=True)
    lxr = pylxr.LXR(map_size_bits=30)
    opr_blocks = {}
    current_block_oprs: List[OPR] = []
    current_height = 0
    pnt_rewards = 0
    for e in reversed(entries):
        if current_height != e["dbheight"]:
            if 10 <= len(current_block_oprs):
                current_block_oprs.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
                opr_blocks[current_height] = current_block_oprs
                current_block_oprs = []
            current_height = e["dbheight"]

        # Check if it's a valid OPR
        # If so, compute it's hash and append to current block OPRs
        entry_hash = bytes.fromhex(e.get("entryhash"))
        external_ids = e.get("extids")
        content = e.get("content")
        opr = OPR.from_entry(entry_hash, external_ids, content)
        if opr is None:
            continue
        opr.opr_hash = lxr.h(content)
        current_block_oprs.append(opr)
    if 10 <= len(current_block_oprs):
        current_block_oprs.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
        opr_blocks[current_height] = current_block_oprs

    # Grade block by block
    previous_winners = ["" for _ in range(10)]
    for height, oprs in opr_blocks.items():
        valid_oprs: List[OPR] = []
        for o in oprs:
            difficulty = lxr.h(o.opr_hash + o.nonce)[:8]
            if difficulty != o.self_reported_difficulty != difficulty:
                print(f"Dishonest OPR difficulty reported at entry: {o.entry_hash}")
                continue
            if o.prev_winners != previous_winners:
                continue
            valid_oprs.append(o)
            if 50 <= len(valid_oprs):
                break  # Found max number of honest submissions, go grade them

        if len(valid_oprs) < 10:
            continue  # Must have at least 10 valid submissions to grade them

        # TODO: opr.RemoveDuplicateSubmissions().
        #       Technically not needed, but should match reference implementation

        # Calculate grade
        for i in range(len(valid_oprs) - 1, -1, -1):
            if i < 10:
                break
            averages = average_estimates(valid_oprs[:i])
            for j in range(i):
                valid_oprs[j].calculate_grade(averages)
            valid_oprs.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
            valid_oprs.sort(key=lambda x: x.grade)

        # Set the previous winners and look for PNT Rewards
        previous_winners = []
        for i, o in enumerate(valid_oprs[:10]):
            previous_winners.append(o.entry_hash[:8].hex())
            if o.coinbase_address == address:
                pnt_rewards += consts.BLOCK_REWARDS.get(i, 0)

    balances[consts.PNT] = pnt_rewards
    print(json.dumps(balances))


@main.command()
@click.argument("fct-address", type=str)
@click.argument("amount", type=float)
@click.option("--testnet", is_flag=True)
@click.option("--dry-run", is_flag=True)
def burn(fct_address, amount, testnet, dry_run):
    """Burn FCT for pFCT"""
    factomd = Factomd()
    try:
        balance = factomd.factoid_balance(fct_address).get("balance")
        balance = balance / consts.FACTOSHIS_PER_FCT
        print(f"Starting balance: {balance} FCT")
    except factom.exceptions.InvalidParams:
        print("Invalid FCT Address")
        return

    if balance < amount:
        print("Error: not enough FCT to fulfill requested conversion")
        return

    walletd = FactomWalletd()
    tx_name = "burn"
    factoshi_burn = int(amount * consts.FACTOSHIS_PER_FCT)
    burn_address = consts.BurnAddresses.MAINNET.value if not testnet else consts.BurnAddresses.TESTNET.value
    print(f"Burning {amount} FCT from {fct_address} to {burn_address}...")
    try:
        walletd.delete_transaction(tx_name)
    except factom.exceptions.InternalError:
        # Transaction just didn't exist
        pass
    walletd.new_transaction(tx_name)
    walletd.add_input(tx_name, factoshi_burn, fct_address)
    walletd.add_ec_output(tx_name, 0, burn_address)
    walletd.sign_transaction(tx_name, force=True)
    tx = walletd.compose_transaction(tx_name)
    if dry_run:
        print("Tx:", json.dumps(tx))
        print("The above transaction was not sent.")
    else:
        tx_response = factomd.factoid_submit(tx["params"]["transaction"])
        print(f"TxID: {tx_response['txid']}")
    walletd.delete_transaction(tx_name)


if __name__ == "__main__":
    main()
