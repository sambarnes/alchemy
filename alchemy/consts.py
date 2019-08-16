from enum import Enum
from typing import Dict

TRANSACTIONS_CHAIN_ID = "77d4651d899bdff0a8e15515ea49552a530b4657bc198414f555aabcde87e5b0"
OPR_CHAIN_ID = "13de39548b56de06a0c4637f6b16852db6fc56749cbd71692ef9af61a2da3247"

START_HEIGHT = 0
FACTOSHIS_PER_FCT = 1e8

BLOCK_REWARDS: Dict[int, int] = {
    0: int(800 * 1e8),
    1: int(600 * 1e8),
    2: int(450 * 1e8),
    3: int(450 * 1e8),
    4: int(450 * 1e8),
    5: int(450 * 1e8),
    6: int(450 * 1e8),
    7: int(450 * 1e8),
    8: int(450 * 1e8),
    9: int(450 * 1e8),
}

PNT = "PNT"
CURRENCY_ASSETS = {"USD", "EUR", "JPY", "GBP", "CAD", "CHF", "INR", "SGD", "CNY", "HKD", "KRW", "BRL", "PHP", "MXN"}
COMMODITY_ASSETS = {"XAU", "XAG", "XPD", "XPT"}
CRYPTO_ASSETS = {"XBT", "ETH", "LTC", "RVN", "XBC", "FCT", "BNB", "XLM", "ADA", "XMR", "DASH", "ZEC", "DCR"}
ALL_PEGGED_ASSETS = CURRENCY_ASSETS.union(COMMODITY_ASSETS).union(CRYPTO_ASSETS)
ALL_ASSETS = ALL_PEGGED_ASSETS.union({PNT})


class BurnAddresses(Enum):
    MAINNET = "EC2BURNFCT2PEGNETooo1oooo1oooo1oooo1oooo1oooo19wthin"
    TESTNET = "EC2BURNFCT2TESTxoooo1oooo1oooo1oooo1oooo1oooo1EoyM6d"
