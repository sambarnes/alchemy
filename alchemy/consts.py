from enum import Enum
from typing import Dict


class BurnAddresses(Enum):
    MAINNET = "EC2BURNFCT2PEGNETooo1oooo1oooo1oooo1oooo1oooo19wthin"
    TESTNET = "EC2BURNFCT2TESTxoooo1oooo1oooo1oooo1oooo1oooo1EoyM6d"


OPR_CHAIN_ID = "13de39548b56de06a0c4637f6b16852db6fc56749cbd71692ef9af61a2da3247"
START_HEIGHT = 1
FACTOSHIS_PER_FCT = 1e8

BLOCK_REWARDS: Dict[int, float] = {0: 800, 1: 600, 2: 450, 3: 450, 4: 450, 5: 450, 6: 450, 7: 450, 8: 450, 9: 450}

PNT = "PNT"
CURRENCY_ASSETS = {"USD", "EUR", "JPY", "GBP", "CAD", "CHF", "INR", "SGD", "CNY", "HKD", "KRW", "BRL", "PHP", "MXN"}
COMMODITY_ASSETS = {"XAU", "XAG", "XPD", "XPT"}
CRYPTO_ASSETS = {PNT, "XBT", "ETH", "LTC", "RVN", "XBC", "FCT", "BNB", "XLM", "ADA", "XMR", "DASH", "ZEC", "DCR"}
ALL_PEGGED_ASSETS = CURRENCY_ASSETS.union(COMMODITY_ASSETS).union(CRYPTO_ASSETS)
