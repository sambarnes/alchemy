# Alchemy

An alternative utility for interacting with the PegNet.

**Kinda ugly, very alpha. Use at your own risk.**

## Features
- Burn FCT for pFCT
- Get FCT, pFCT, and PNT balances (well... all of them really, but they're still 0 :D)

## Prerequisites
- Make sure to have a LXR map generated already, 
- Install the [pylxr](https://github.com/pegnet/pylxr) module to your python virtual environment 

## Usage
*(Note: all commands currently assume locally running factomd and factom-walletd instances)*
```
$ ./alchemy.py
Usage: alchemy.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  burn          Burn FCT for pFCT
  get-balances  Get a list of all balances for the given address
  run           Main entry point for the node
```

### Burning FCT for pFCT
This command will take a given FCT address that you have stored in factom-walletd, and create a transaction of the specified amount to be burned for pFCT.

Example:
```
$ ./alchemy.py burn FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q 30

Starting balance: 39809.90816 FCT
Burning 30.0 FCT from FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q to EC2BURNFCT2PEGNETooo1oooo1oooo1oooo1oooo1oooo19wthin...
TxID: fd9b77c9b25a5b37e0b9f56bc060dc12cd2c6405e3608e8a1cd44b4d8e89ff65
```

Optionally, you can run with `--dry-run` to simply compose the transaction and return without broadcasting it:
```
$ ./alchemy.py burn FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q 30 --dry-run

Starting balance: 39779.90816 FCT
Burning 30.0 FCT from FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q to EC2BURNFCT2PEGNETooo1oooo1oooo1oooo1oooo1oooo19wthin...
Tx: {"jsonrpc": "2.0", "id": 15, "params": {"transaction": "02016c40e7777d0100018b96c1bc00646f3e8750c550e4582eca5047546ffef89c13a175985e320232bacac81cc4280037399721298d77984585040ea61055377039a4c3f3e2cd48c46ff643d50fd64f01718b5edd2914acc2e4677f336c1a32736e5e9bde13663e6413894f57ec272e285c500f77e0975099512cc53a27591fa9bc09a7a972d07d645a15034d55361e6ff805da5113bbf604de7cf19f601702c8ca2efad22d18059be72b940679560f0d"}, "method": "factoid-submit"}
The above transaction was not sent.
```

### Checking current balances
Currently only FCT and pFCT are supported:
```
$ ./alchemy.py get-balances FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q | jq

{
  "pINR": 0,
  "pCNY": 0,
  "pXAG": 0,
  "pMXN": 0,
  "pXBC": 0,
  "pPHP": 0,
  "pFCT": 120,
  "pHKD": 0,
  "pDASH": 0,
  "pRVN": 0,
  "pCHF": 0,
  "pXPD": 0,
  "pETH": 0,
  "pBNB": 0,
  "pXAU": 0,
  "pZEC": 0,
  "pUSD": 0,
  "pXBT": 0,
  "pBRL": 0,
  "pLTC": 0,
  "pKRW": 0,
  "pXPT": 0,
  "pSGD": 0,
  "pADA": 0,
  "pXMR": 0,
  "pJPY": 0,
  "pEUR": 0,
  "pCAD": 0,
  "pXLM": 0,
  "pDCR": 0,
  "pGBP": 0,
  "FCT": 39779.90816,
  "PNT": 60000,
}
```
