# Alchemy

An alternative utility for interacting with the PegNet.

**Kinda ugly, very alpha. Use at your own risk.**

## Features
- Grades all OPR records and validates factoid burns
- Create burn transactions (FCT --> pFCT)
- Get FCT, pFCT, and PNT balances

## Prerequisites
- Make sure to have a LXR map generated already, it'll take far far too long for the naive python implementation to generate it
- Install the [pylxr](https://github.com/pegnet/pylxr) module to your python virtual environment 

## Usage
*(Note: all commands currently assume locally running factomd and factom-walletd instances)*
```
$ ./alchemy.py
Usage: alchemy.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  burn              Burn FCT for pFCT
  get-balances      Get a list of all balances for the given address
  get-factoid-head  Get the highest Factoid block parsed
  get-opr-head      Get the highest OPR Entry block parsed
  get-winners       Get winning records at the given block height
  reset             Delete the current alchemy database
  run               Main entry point for the node
```

### Running the Grader
This command will grade all unseen oracle price records and run through all unseen Factoid Blocks looking for burn transactions. Stores results in a database to save progress and make subsequent runs quicker. It will also launch a MessagePack based RPC server for the CLI to utilize

Example:
```
$ ./alchemy.py run

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


Current Factom block height: 145
Dispatched tasks. Sleeping for 1 minute...


Highest OPR Entry Block previously parsed: 142
Graded OPR block 143 (winners: ['c48d70ccdbc9121a', '1b2b21b3d49894f7', '6d1abd9da09957ec', '10ef6812a03c56b9', 'cb0928ad73503bed', '124d5e51cd6d91d0', '27cb90f0d1650e4b', 'fb90b47f8f16ec0c', 'f0112da0392382fb', '3d494c4d09664c87'])
Graded OPR block 144 (winners: ['10a7585cdd6659ba', 'b4bcabd1eaf69de7', '47a7616fd2ca5626', '545282d63903cd25', '0eb46244b22bc153', 'b398ddeb36071c16', 'dcf1636ede1341d7', 'facccd20bf5cb633', '9f314e621a306595', '5c7609b303734f85'])
Graded OPR block 145 (winners: ['b1e805e484c6280b', '2179a18295d0dca6', '776170efe152cd76', '152b25b16ba178be', '3483dd3c63ba6b9a', 'f1100f6eb334c547', '69f55d349d7f0696', '75e8bbc3466f1680', '09a2a99677c014f5', '3acf9f917284774c'])
Finished grading all unseen blocks
Updating OPR database...

Highest Factoid Block previously parsed: 142
Parsed factoid block 143 (burns found: 0)
Parsed factoid block 144 (burns found: 0)
Parsed factoid block 145 (burns found: 0)
Updating FCT burn database...
```

### Burning FCT for pFCT
This command will take a given FCT address that you have stored in factom-walletd, and create a transaction of the specified amount to be burned for pFCT.

Example:
```
$ ./alchemy.py burn 30 FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q

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
Currently only FCT, pFCT, and PNT are supported:
```
$ ./alchemy.py get-balances FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q | jq

{
  "pFCT": 120,
  "FCT": 39779.90816,
  "PNT": 60000,
}
```


### Get winning records of a block
Returns a list of entry hashes for the winners of the given block height

Example:
```
$ ./alchemy.py get-winners 76 | jq
{
  "winners": [
    {
      "place": 1,
      "entry_hash": "82426bf90f76c69cdf7d3fb877aed7fd2b5f7c823b400791927827d59a29b2c7"
    },
    {
      "place": 2,
      "entry_hash": "e7b511c78cd080d45e8d3c4bb8e419bcb8d2840bc8d4cb7f41acf9797cea0ece"
    },
    {
      "place": 3,
      "entry_hash": "ae4f73fe65e0a7e8f4cfcec54ea02bbdeff84b50a5fd0d8e748a8d4e24ef7219"
    },
    {
      "place": 4,
      "entry_hash": "547bcd4bfd08468642fa0472cd8f1a244859f74e0288f4354eb444abfd9d6375"
    },
    {
      "place": 5,
      "entry_hash": "3e363b762d258a6dd1b3810ac826fe3a2dca418506f36fcefc6e391cdff816bb"
    },
    {
      "place": 6,
      "entry_hash": "a38ca5cd6cc27db2038f1634f42defe9068727ee780e40df37b74247eaf9d42a"
    },
    {
      "place": 7,
      "entry_hash": "ca8335119520a986ba73fe18ff3d16bbca3772623f0a8a198aaf6f32e7e89096"
    },
    {
      "place": 8,
      "entry_hash": "818b97a31388b9e51d3970cbf8cba934831c4c94eda1c756e92bb08fd87079ad"
    },
    {
      "place": 9,
      "entry_hash": "78fd2d597c9f6bc72b99af2e774753bb900ece7e7ba3defef184dfb0f022e18e"
    },
    {
      "place": 10,
      "entry_hash": "538add19330dfd6e11b622e309bf8c79d14152bc6a57bd798c92dee48f841200"
    }
  ]
}
```