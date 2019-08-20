import csv
import datetime
import numpy as np
import os

import alchemy.consts as consts

home = os.getenv("HOME")
prices_path = f"{home}/.pegnet/alchemy/prices/"
prices_filename = f"{prices_path}/data.csv"
difficulties_path = f"{home}/.pegnet/alchemy/difficulties/"
difficulties_filename = f"{difficulties_path}/data.csv"


def write_prices(prices, height, timestamp):
    if not os.path.exists(prices_path):
        os.makedirs(prices_path)
    headers = ["Date", "Height"] + sorted(list(consts.ALL_ASSETS))
    row = prices
    row["Date"] = np.datetime64(datetime.datetime.utcfromtimestamp(timestamp))
    row["Height"] = height
    if os.path.exists(prices_filename):
        with open(prices_filename, "a") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writerow(row)
    else:
        with open(prices_filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow(row)


def write_difficulty(top_record, bottom_record):
    if not os.path.exists(difficulties_path):
        os.makedirs(difficulties_path)
    row = {
        "Date": np.datetime64(datetime.datetime.utcfromtimestamp(top_record.timestamp)),
        "Height": top_record.height,
        "Top": int.from_bytes(top_record.self_reported_difficulty, byteorder="big"),
        "Bottom": int.from_bytes(bottom_record.self_reported_difficulty, byteorder="big"),
    }
    if os.path.exists(difficulties_filename):
        with open(difficulties_filename, "a") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)
    else:
        with open(difficulties_filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)
