import json
import plyvel
import os
import struct
from typing import Dict, List, Union


OPR_HEAD = b"OPRHead"
FACTOID_HEAD = b"FactoidHead"
BALANCES = b"Balances"
WINNERS = b"Winners"

BalanceMap = Dict[str, float]


class AlchemyDB:
    def __init__(self, path: str = None, **kwargs):
        """
        An alchemy specific wrapper around level-db

        :param path: file-path to the leveldb database, defaults to: /$HOME/.pegnet/alchemy/data/
        """
        if path is None:
            home = os.getenv("HOME")
            path = f"{home}/.pegnet/alchemy/data/"
        if not os.path.exists(path):
            os.makedirs(path)
        self._db = plyvel.DB(path, **kwargs)

    def close(self):
        self._db.close()

    def get_opr_head(self) -> int:
        height_bytes = self._db.get(OPR_HEAD)
        return -1 if height_bytes is None else struct.unpack(">I", height_bytes)[0]

    def put_opr_head(self, height: int):
        height_bytes = struct.pack(">I", height)
        self._db.put(OPR_HEAD, height_bytes)

    def get_factoid_head(self) -> int:
        height_bytes = self._db.get(FACTOID_HEAD)
        return -1 if height_bytes is None else struct.unpack(">I", height_bytes)[0]

    def put_factoid_head(self, height: int):
        height_bytes = struct.pack(">I", height)
        self._db.put(FACTOID_HEAD, height_bytes)

    def get_balances(self, address: bytes):
        sub_db = self._db.prefixed_db(BALANCES)
        balances_bytes = sub_db.get(address)
        return None if balances_bytes is None else json.loads(balances_bytes.decode())

    def put_balances(self, address: bytes, balances: BalanceMap):
        sub_db = self._db.prefixed_db(BALANCES)
        balance_bytes = json.dumps(balances).encode()
        sub_db.put(address, balance_bytes)

    def update_balances(self, address: bytes, deltas: BalanceMap):
        balances = self.get_balances(address)
        if balances is not None:
            for k, v in deltas.items():
                balances[k] += v
        self.put_balances(address, balances)

    def get_winners(self, height: int):
        sub_db = self._db.prefixed_db(WINNERS)
        height_bytes = struct.pack(">I", height)
        winners_bytes = sub_db.get(height_bytes)
        return [] if winners_bytes is None else [winners_bytes[i:i+32] for i in range(0, 10, 32)]

    def put_winners(self, height: int, winners: List[bytes]):
        sub_db = self._db.prefixed_db(WINNERS)
        height_bytes = struct.pack(">I", height)
        winners_bytes = b"".join(winners)
        sub_db.put(height_bytes, winners_bytes)
