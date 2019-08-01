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
  burn          Burn FCT for pFCT
  get-balances  Get a list of all balances for the given address
  get-winners   Get winning records at the given block height
  run           Main entry point for the node
```

### Running the Grader
This command will grade all unseen oracle price records and run through all unseen Factoid Blocks looking for burn transactions. Stores results in a database to save progress and make subsequent runs quicker.

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

Current Factom block height: 218

Highest OPR Entry Block previously parsed: 167
Finished grading all unseen blocks
Updating database...

Highest Factoid Block previously parsed: 213
Finding burn transactions in factoid block 214...
Finding burn transactions in factoid block 215...
Finding burn transactions in factoid block 216...
Finding burn transactions in factoid block 217...
Finding burn transactions in factoid block 218...
Updating database...

Done.
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