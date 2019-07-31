#!/usr/bin/env python3.7

import click
import factom
import json
import pylxr
from factom_keys.fct import FactoidAddress
from factom import Factomd, FactomWalletd

import burning
import consts
import db
import grading


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

    factomd = Factomd()
    lxr = pylxr.LXR(map_size_bits=30)
    database = db.AlchemyDB(create_if_missing=True)

    latest_block = factomd.heights()['directoryblockheight']
    print(f"Current Factom block height: {latest_block}")

    grading.run(factomd, lxr, database)


@main.command()
@click.argument("address", type=str)
@click.option("--testnet", is_flag=True)
def get_balances(address, testnet):
    """Get a list of all balances for the given address"""
    factomd = Factomd()
    database = db.AlchemyDB(create_if_missing=True)
    try:
        fct_balance = factomd.factoid_balance(address).get("balance")
    except factom.exceptions.InvalidParams:
        print("Invalid Address")
        return

    # Run through the latest factoid blocks for new burns
    burning.run(factomd, database, testnet)
    address_bytes = FactoidAddress(address_string=address).rcd_hash
    balances = database.get_balances(address_bytes)
    if balances is None:
        network_ticker = "p" if not testnet else "t"
        balances = {f"{network_ticker}{ticker}": 0 for ticker in consts.ALL_PEGGED_ASSETS}
    balances["FCT"] = fct_balance
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
