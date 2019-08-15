#!/usr/bin/env python3.7

import click
import factom
import json
from factom import Factomd, FactomWalletd
from typing import List

import alchemy.main
import alchemy.consts as consts
import alchemy.rpc
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
    alchemy.main.run(testnet)


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
@click.confirmation_option(prompt="Are you sure you want to reset the database?")
def reset():
    """Delete the current alchemy database"""
    import os
    import shutil

    home = os.getenv("HOME")
    path = f"{home}/.pegnet/alchemy/"
    shutil.rmtree(path, ignore_errors=True)
    print(f"Deleted database at: {path}")


# --------------------------------------------------------------------------------
# RPC Wrapper Commands


@main.command()
def get_opr_head():
    """Get the highest OPR Entry block parsed"""
    result = alchemy.rpc.get_opr_head()
    print(json.dumps(result))


@main.command()
def get_factoid_head():
    """Get the highest Factoid block parsed"""
    result = alchemy.rpc.get_factoid_head()
    print(json.dumps(result))


@main.command()
@click.argument("height", type=int)
def get_winners(height):
    """Get winning records at the given block height"""
    result = alchemy.rpc.get_winners(height)
    print(json.dumps(result))


@main.command()
@click.argument("address", type=str)
@click.option("--testnet", is_flag=True)
@click.option("--human", is_flag=True)
def get_balances(address, testnet, human):
    """Get a list of all balances for the given address"""
    result = alchemy.rpc.get_balances(address)
    if human:
        result["balances"] = {ticker: value / 1e8 for ticker, value in result["balances"].items()}
    print(json.dumps(result))


@main.command()
@click.option("--ticker", "-t", type=str, multiple=True)
@click.option("--by-height", is_flag=True)
def graph_prices(ticker, by_height):
    """Show a graph for the prices of given tickers"""
    for t in ticker:
        if t not in consts.ALL_ASSETS:
            print(f"Invalid ticker symbol: {t}\n")
            print(f"Possible values: {consts.ALL_ASSETS}")
            return
    if len(ticker) == 0:
        ticker = sorted(consts.ALL_ASSETS)

    alchemy.rpc.graph_prices(ticker, by_height)
    print("Done. A browser window should open shortly.")


@main.command()
@click.option("--by-height", is_flag=True)
def graph_difficulties(by_height):
    """Show a graph for the range of winning miner difficulties"""
    alchemy.rpc.graph_difficulties(by_height)
    print("Done. A browser window should open shortly.")


if __name__ == "__main__":
    main()
