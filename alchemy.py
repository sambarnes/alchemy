#!/usr/bin/env python3.7

import click
import factom
import json
import pylxr
from factom_keys.fct import FactoidAddress
from factom import Factomd, FactomWalletd

import alchemy.burning
import alchemy.consts as consts
import alchemy.grading
from alchemy.db import AlchemyDB


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
@click.option("--testnet", is_flag=True)
def run(testnet):
    """Main entry point for the node"""
    print(HEADER)

    factomd = Factomd()
    lxr = pylxr.LXR(map_size_bits=30)
    database = AlchemyDB(testnet, create_if_missing=True)

    latest_block = factomd.heights()["directoryblockheight"]
    print(f"Current Factom block height: {latest_block}")

    alchemy.grading.run(factomd, lxr, database, testnet)
    alchemy.burning.find_new_burns(factomd, database, testnet)
    print("\nDone.")


@main.command()
@click.argument("address", type=str)
@click.option("--testnet", is_flag=True)
def get_balances(address, testnet):
    """Get a list of all balances for the given address"""
    factomd = Factomd()
    database = AlchemyDB(testnet, create_if_missing=True)
    try:
        fct_balance = factomd.factoid_balance(address).get("balance")
    except factom.exceptions.InvalidParams:
        print("Invalid Address")
        return

    address_bytes = FactoidAddress(address_string=address).rcd_hash
    balances = database.get_balances(address_bytes)
    if balances is None:
        balances = {}
    balances["FCT"] = fct_balance
    print(json.dumps({"balances": balances}))


@main.command()
@click.argument("amount", type=float)
@click.argument("fct-address", type=str)
@click.option("--testnet", is_flag=True)
@click.option("--dry-run", is_flag=True)
def burn(amount, fct_address, testnet, dry_run):
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
        pass  # Transaction just didn't exist

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


@main.command()
@click.argument("height", type=int)
@click.option("--testnet", is_flag=True)
def get_winners(height, testnet):
    """Get winning records at the given block height"""
    database = AlchemyDB(testnet, create_if_missing=True)
    winning_entry_hashes = database.get_winners(height)
    winners = (
        [{"place": i + 1, "entry_hash": entry_hash.hex()} for i, entry_hash in enumerate(winning_entry_hashes)]
        if len(winning_entry_hashes) != 0
        else None
    )
    print(json.dumps({"winners": winners}))


if __name__ == "__main__":
    main()
