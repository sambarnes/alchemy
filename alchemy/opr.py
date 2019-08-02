import factom_keys.fct
import json
import numpy as np
from dataclasses import dataclass
from typing import Dict, List

import alchemy.consts as consts


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

    @classmethod
    def from_entry(cls, entry_hash: bytes, external_ids: list, content: bytes):
        if type(entry_hash) != bytes or len(entry_hash) != 32:
            return None
        if len(external_ids) != 2:
            return None
        try:
            record_json = json.loads(content.decode())
        except ValueError:
            return None

        nonce = external_ids[0]
        self_reported_difficulty = external_ids[1]
        if type(nonce) != bytes or type(self_reported_difficulty) != bytes:
            return None

        coinbase = record_json.get("coinbase")
        if not factom_keys.fct.FactoidAddress.is_valid(coinbase):
            return None

        height = record_json.get("dbht")
        if type(height) != int or height < 0:
            return None

        miner_id = record_json.get("minerid")
        if type(miner_id) != str:
            return None

        prev_winners = record_json.get("winners")
        if type(prev_winners) != list or len(prev_winners) != 10:
            return None
        for winner in prev_winners:
            if type(winner) != str:
                return

        # Check that the OPR has all required assets (and no more)
        asset_estimates = record_json.get("assets")
        if type(asset_estimates) != dict or len(asset_estimates.keys()) != len(consts.ALL_PEGGED_ASSETS):
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
