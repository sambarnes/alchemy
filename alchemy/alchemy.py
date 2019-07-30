#!/usr/bin/env python3.7

import click
import consts
import factom.exceptions
import json
from factom import Factomd, FactomWalletd

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
    expected_burn_address = (
        consts.BurnAddresses.MAINNET.value
        if not testnet
        else consts.BurnAddresses.TESTNET.value
    )
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

    # TODO: Parse OPR Chain for PNT rewards

    balances[f"{network_ticker}FCT"] = factoshis_burned / consts.FACTOSHIS_PER_FCT
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
    burn_address = (
        consts.BurnAddresses.MAINNET.value
        if not testnet
        else consts.BurnAddresses.TESTNET.value
    )
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
