#!/usr/bin/env python3.7

import click
import factom
import json
from factom import Factomd, FactomWalletd
from factom_keys.ec import ECAddress, ECPrivateKey
from factom_keys.fct import FactoidAddress, FactoidPrivateKey
from typing import List

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
@click.argument("amount", type=int)
@click.argument("from_ticker", type=str)
@click.argument("address", type=str)
@click.option("--to", "-t", required=True, multiple=True, type=(int, str))
@click.option("--ec-address", "-e", required=True, type=str)
@click.option("--dry-run", is_flag=True)
def convert(amount, from_ticker, address, to, ec_address, dry_run):
    """Perform a conversion between assets"""
    # Input validation
    if from_ticker[0] != "p" or from_ticker[1:] not in consts.ALL_ASSETS:
        print(f"Error: invalid ticker symbol ({from_ticker})\n")
        print(f"Possible values: {consts.ALL_ASSETS}")
        return
    if not FactoidAddress.is_valid(address):
        print(f"Error: invalid source address ({address}), must be a valid Factoid address")
        return
    if not ECAddress.is_valid(ec_address):
        print(f"Error: invalid EC address ({ec_address})")
        return
    from_ticker = from_ticker[1:]

    # Get the singer private key from walletd
    factomd = Factomd()
    walletd = FactomWalletd()
    try:
        address_secret_string = walletd.address(address)["secret"]
    except factom.exceptions.InternalError:
        print(f"Error: Factoid address ({address}) not found in wallet")
        return

    input_signer = FactoidPrivateKey(key_string=address_secret_string)
    tx = alchemy.transactions.models.Transaction()
    tx.set_input(address=input_signer.get_factoid_address(), asset_type=from_ticker, amount=amount)

    output_address = input_signer.get_factoid_address()
    for amount, ticker in to:
        if ticker[0] != "p" or ticker[1:] not in consts.ALL_ASSETS:
            print(f"Error: invalid ticker symbol ({ticker})\n")
            print(f"Possible values: {consts.ALL_ASSETS}")
            return
        t = ticker[1:]
        tx.add_output(address=output_address, asset_type=t, amount=amount)

    tx_entry = alchemy.transactions.models.TransactionEntry()
    tx_entry.add_transaction(tx)
    tx_entry.add_signer(input_signer)
    external_ids, content = tx_entry.sign()

    if dry_run:
        print(f"External-IDs: {[x.hex() for x in external_ids]}")
        print(f"Content: {content.decode()}")
        print("The above transaction was not sent.")
        return

    response = walletd.new_entry(
        factomd=factomd,
        chain_id=consts.TRANSACTIONS_CHAIN_ID,
        ext_ids=external_ids,
        content=content,
        ec_address=ec_address,
    )
    print(f"Tx Sent: {response}")


@main.command()
@click.argument("amount", type=int)
@click.argument("from_ticker", type=str)
@click.argument("address", type=str)
@click.option("--to", "-t", required=True, multiple=True, type=(int, str))
@click.option("--ec-address", "-e", required=True, type=str)
@click.option("--dry-run", is_flag=True)
def send(amount, from_ticker, address, to, ec_address, dry_run):
    """Send a like-kind transaction"""
    # Input validation
    if from_ticker[0] != "p" or from_ticker[1:] not in consts.ALL_ASSETS:
        print(f"Error: invalid ticker symbol ({from_ticker})\n")
        print(f"Possible values: {consts.ALL_ASSETS}")
        return
    if not FactoidAddress.is_valid(address):
        print(f"Error: invalid source address ({address}), must be a valid Factoid address")
        return
    if not ECAddress.is_valid(ec_address):
        print(f"Error: invalid EC address ({ec_address})")
        return
    from_ticker = from_ticker[1:]

    # Get the singer private key from walletd
    factomd = Factomd()
    walletd = FactomWalletd()
    try:
        address_secret_string = walletd.address(address)["secret"]
    except factom.exceptions.InternalError:
        print(f"Error: Factoid address ({address}) not found in wallet")
        return

    input_signer = FactoidPrivateKey(key_string=address_secret_string)
    tx = alchemy.transactions.models.Transaction()
    tx.set_input(address=input_signer.get_factoid_address(), asset_type=from_ticker, amount=amount)

    input_remaining = amount
    for output_amount, output_address in to:
        if input_remaining < output_amount:
            print(f"Error: not enough inputs to cover outputs")
        if not FactoidAddress.is_valid(output_address):
            print(f"Error: invalid output address ({output_address})")
            return
        tx.add_output(address=FactoidAddress(address_string=output_address), amount=output_amount)
        input_remaining -= output_amount

    tx_entry = alchemy.transactions.models.TransactionEntry()
    tx_entry.add_transaction(tx)
    tx_entry.add_signer(input_signer)
    external_ids, content = tx_entry.sign()

    if dry_run:
        print(f"External-IDs: {[x.hex() for x in external_ids]}")
        print(f"Content: {content.decode()}")
        print("The above transaction was not sent.")
        return

    response = walletd.new_entry(
        factomd=factomd,
        chain_id=consts.TRANSACTIONS_CHAIN_ID,
        ext_ids=external_ids,
        content=content,
        ec_address=ec_address,
    )
    print(f"Tx Sent: {response}")


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
