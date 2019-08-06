import csv
import datetime
import numpy as np
import os

import alchemy.consts as consts

path = f"{os.getenv('HOME')}/.pegnet/alchemy/prices/"
filename = f"{path}/data.csv"


def write(record):
    if not os.path.exists(path):
        os.makedirs(path)
    headers = ["Date", "Height"] + list(consts.ALL_PEGGED_ASSETS)
    row = record.asset_estimates
    row["Date"] = np.datetime64(datetime.datetime.utcfromtimestamp(record.timestamp))
    row["Height"] = record.height
    if os.path.exists(filename):
        with open(filename, "a") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writerow(row)
    else:
        with open(filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow(row)
