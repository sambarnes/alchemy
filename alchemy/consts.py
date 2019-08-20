from enum import Enum
from typing import Dict

TRANSACTIONS_CHAIN_ID = "77d4651d899bdff0a8e15515ea49552a530b4657bc198414f555aabcde87e5b0"
OPR_CHAIN_ID = "a642a8674f46696cc47fdb6b65f9c87b2a19c5ea8123b3d2f0c13b6f33a9d5ef"

START_HEIGHT = 206421
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

# Due to the nature of float arithmetic, we must grade OPRs with the exact order of tokens listed here
ASSET_GRADING_ORDER = [
    "PNT",
    "USD",
    "EUR",
    "JPY",
    "GBP",
    "CAD",
    "CHF",
    "INR",
    "SGD",
    "CNY",
    "HKD",
    "KRW",
    "BRL",
    "PHP",
    "MXN",
    "XAU",
    "XAG",
    "XPD",
    "XPT",
    "XBT",
    "ETH",
    "LTC",
    "RVN",
    "XBC",
    "FCT",
    "BNB",
    "XLM",
    "ADA",
    "XMR",
    "DASH",
    "ZEC",
    "DCR",
]


class BurnAddresses(Enum):
    MAINNET = "EC2BURNFCT2PEGNETooo1oooo1oooo1oooo1oooo1oooo19wthin"
    TESTNET = "EC2BURNFCT2TESTxoooo1oooo1oooo1oooo1oooo1oooo1EoyM6d"
