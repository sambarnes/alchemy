from enum import Enum


class BurnAddresses(Enum):
    MAINNET = "EC2BURNFCT2PEGNETooo1oooo1oooo1oooo1oooo1oooo19wthin"
    TESTNET = "EC2BURNFCT2TESTxoooo1oooo1oooo1oooo1oooo1oooo1EoyM6d"


OPR_CHAIN_ID = "fafedb5fb8e7d1512244b683608f0b248326f1b8fae497058ba8ae8d577e9c14"
START_HEIGHT = 1
FACTOSHIS_PER_FCT = 1e8


PNT = "PNT"
CURRENCY_ASSETS = {
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
}
COMMODITY_ASSETS = {"XAU", "XAG", "XPD", "XPT"}
CRYPTO_ASSETS = {
    PNT,
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
}
ALL_PEGGED_ASSETS = CURRENCY_ASSETS.union(COMMODITY_ASSETS).union(CRYPTO_ASSETS)
