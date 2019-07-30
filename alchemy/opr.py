import factom_keys.fct
import json
import math
from dataclasses import dataclass
from typing import Dict, List

import consts


AssetEstimates = Dict[str, float]


@dataclass
class OPR:
    entry_hash: bytes
    nonce: bytes
    self_reported_difficulty: bytes
    coinbase_address: str
    height: str
    asset_estimates: AssetEstimates
    prev_winners: List[str]
    miner_id: str

    grade: float = math.inf
    opr_hash: bytes = bytes(32)

    def calculate_grade(self, averages: AssetEstimates):
        self.grade = 0
        for k, v in self.asset_estimates.items():
            if averages[k] > 0:
                # compute the difference from the average
                d = (v - averages[k]) / averages[k]
                # the grade is the sum of the square of the square of the differences
                self.grade = self.grade + d * d * d * d

    @classmethod
    def from_entry(cls, entry_hash: bytes, external_ids: list, content: bytes):
        if len(external_ids) != 2:
            return None
        try:
            d = json.loads(content.decode())
        except ValueError:
            return None

        nonce = external_ids[0]
        self_reported_difficulty = external_ids[1]
        coinbase = d.get("coinbase")
        asset_estimates = d.get("assets")
        height = d.get("dbht")
        prev_winners = d.get("winners")
        miner_id = d.get("minerid")

        # Basic type validation
        if not factom_keys.fct.FactoidAddress.is_valid(coinbase):
            return None
        if type(asset_estimates) != dict or type(height) != int or type(prev_winners) != list:
            return None
        if type(miner_id) != str:
            return None
        for winner in prev_winners:
            if type(winner) != str:
                return

        # Check that the OPR has all required assets (and no more)
        if len(asset_estimates.keys()) != len(consts.ALL_PEGGED_ASSETS):
            return None
        for k, v in asset_estimates.items():
            if type(k) != str or type(v) not in {int, float}:
                return None
            if k != consts.PNT and v == 0:
                return None
        for k in consts.ALL_PEGGED_ASSETS:
            if k not in asset_estimates:
                return None

        return OPR(
            entry_hash=entry_hash,
            nonce=nonce,
            self_reported_difficulty=self_reported_difficulty,
            coinbase_address=coinbase,
            height=height,
            asset_estimates=asset_estimates,
            prev_winners=prev_winners,
            miner_id=miner_id,
        )


def average_estimates(oprs: List[OPR]) -> AssetEstimates:
    """Computes the average answer for the price of each token reported"""
    averages: AssetEstimates = {k: 0 for k in consts.ALL_PEGGED_ASSETS}
    # Sum up all the prices
    for opr in oprs:
        for k, v in opr.asset_estimates.items():
            # Make sure no OPR has negative values for assets.  Simply treat all values as positive.
            averages[k] += abs(v)
    # Then divide the prices by the number of OraclePriceRecord records.  Two steps is actually faster
    # than doing everything in one loop (one divide for every asset rather than one divide
    # for every asset * number of OraclePriceRecords)  There is also a little bit of a precision advantage
    # with the two loops (fewer divisions usually does help with precision) but that isn't likely to be
    # interesting here.
    oprs_length = float(len(oprs))
    for i in averages:
        averages[i] = averages[i] / oprs_length
    return averages
