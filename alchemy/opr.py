import factom_keys.fct
import json
import numpy as np
from dataclasses import dataclass
from typing import Dict, List

import consts


AssetEstimates = Dict[str, np.float64]


@dataclass
class OPR:
    entry_hash: bytes
    nonce: bytes
    self_reported_difficulty: bytes
    coinbase_address: str
    height: int
    asset_estimates: AssetEstimates
    prev_winners: List[str]
    miner_id: str

    grade: np.float64 = np.inf
    opr_hash: bytes = bytes(32)

    def calculate_grade(self, averages: AssetEstimates):
        self.grade = np.float64(0)
        for k, v in self.asset_estimates.items():
            if averages[k] > 0:
                # compute the difference from the average
                d = (v - averages[k]) / averages[k]
                # the grade is the sum of the square of the square of the differences
                self.grade += np.float64(d * d * d * d)

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
