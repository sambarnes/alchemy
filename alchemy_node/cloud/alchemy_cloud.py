#!/usr/bin/env python3.7

import click
import factom
import json
from factom import Factomd, FactomWalletd
from factom_keys.ec import ECAddress, ECPrivateKey
from factom_keys.fct import FactoidAddress, FactoidPrivateKey

import alchemy.main
import alchemy.consts as consts
import alchemy.rpc
import alchemy.transactions.models


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
    alchemy.main.run(testnet, is_cloud=True)


@main.command()
@click.confirmation_option(prompt="Are you sure you want to reset the database?")
def reset():
    """Delete the current alchemy database"""
    pass


# --------------------------------------------------------------------------------
# RPC Wrapper Commands


@main.command()
def get_sync_head():
    """Get the highest block parsed"""
    try:
        result = alchemy.rpc.get_sync_head()
    except ConnectionRefusedError:
        print("Error: failed to make request, ensure alchemy is running")
        return
    print(json.dumps(result))


@main.command()
@click.argument("height", required=False, type=int)
def get_winners(height):
    """Get winning records at the given block height"""
    try:
        result = alchemy.rpc.get_winners(height)
    except ConnectionRefusedError:
        print("Error: failed to make request, ensure alchemy is running")
        return
    print(json.dumps(result))


@main.command()
@click.argument("address", type=str)
@click.option("--testnet", is_flag=True)
@click.option("--human", is_flag=True)
def get_balances(address, testnet, human):
    """Get a list of all balances for the given address"""
    try:
        result = alchemy.rpc.get_balances(address)
    except ConnectionRefusedError:
        print("Error: failed to make request, ensure alchemy is running")
        return
    if human:
        result["balances"] = {ticker: value / 1e8 for ticker, value in result["balances"].items()}
    print(json.dumps(result))


@main.command()
@click.argument("height", type=int)
def get_rates(height):
    """Get a list of conversion rates for the given block"""
    try:
        result = alchemy.rpc.get_rates(height)
    except ConnectionRefusedError:
        print("Error: failed to make request, ensure alchemy is running")
        return
    print(json.dumps(result))


@main.command()
@click.option("--ticker", "-t", type=str, multiple=True)
@click.option("--by-height", is_flag=True)
def graph_prices(ticker, by_height):
    """Graph the prices of given tickers"""
    for t in ticker:
        if t not in consts.ALL_ASSETS:
            print(f"Invalid ticker symbol: {t}\n")
            print(f"Possible values: {consts.ALL_ASSETS}")
            return
    if len(ticker) == 0:
        ticker = sorted(consts.ALL_ASSETS)

    alchemy.rpc.graph_prices(ticker, by_height, show=True)
    print("Done. A browser window should open shortly.")


@main.command()
@click.option("--by-height", is_flag=True)
def graph_difficulties(by_height):
    """Graph the range of winning miner difficulties"""
    alchemy.rpc.graph_difficulties(by_height, show=True)
    print("Done. A browser window should open shortly.")


if __name__ == "__main__":
    main()
