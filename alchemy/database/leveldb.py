import json
import plyvel
import os
import struct
from factom_keys.fct import FactoidAddress
from typing import Dict, List, Union

from alchemy.database import AlchemyDB


SYNC_HEAD = b"SyncHead"
WINNERS_HEAD = b"WinnersHead"
BALANCES = b"Balances"
WINNERS = b"Winners"
RATES = b"Rates"


class AlchemyLevelDB(AlchemyDB):
    def __init__(self, is_testnet: bool = False, **kwargs):
        """An alchemy specific wrapper around level-db"""
        home = os.getenv("HOME")
        data_dir = "data" if not is_testnet else "data-testnet"
        path = f"{home}/.pegnet/alchemy/{data_dir}/"
        if not os.path.exists(path):
            os.makedirs(path)
        self._db = plyvel.DB(path, **kwargs)

    def close(self):
        self._db.close()

    def get_sync_head(self) -> int:
        height_bytes = self._db.get(SYNC_HEAD)
        return -1 if height_bytes is None else struct.unpack(">I", height_bytes)[0]

    def put_sync_head(self, height: int):
        height_bytes = struct.pack(">I", height)
        self._db.put(SYNC_HEAD, height_bytes)

    def get_balances(self, address: Union[bytes, str]) -> Union[None, Dict[str, int]]:
        sub_db = self._db.prefixed_db(BALANCES)
        if type(address) == str:
            address = FactoidAddress(address_string=address).rcd_hash
        balances_bytes = sub_db.get(address)
        return {} if balances_bytes is None else json.loads(balances_bytes.decode())

    def put_balances(self, address: bytes, balances: Dict[str, int]):
        sub_db = self._db.prefixed_db(BALANCES)
        balance_bytes = json.dumps(balances).encode()
        sub_db.put(address, balance_bytes)

    def update_balances(self, address: bytes, deltas: Dict[str, int]):
        balances = self.get_balances(address)
        if balances is not None:
            for k, v in deltas.items():
                if k in balances:
                    balances[k] += v
                else:
                    balances[k] = v
            self.put_balances(address, balances)
        else:
            self.put_balances(address, deltas)

    def get_winners_head(self) -> int:
        height_bytes = self._db.get(WINNERS_HEAD)
        return -1 if height_bytes is None else struct.unpack(">I", height_bytes)[0]

    def put_winners_head(self, height: int):
        height_bytes = struct.pack(">I", height)
        self._db.put(WINNERS_HEAD, height_bytes)

    def get_winners(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        sub_db = self._db.prefixed_db(WINNERS)
        height_bytes = struct.pack(">I", height)
        winners_bytes = sub_db.get(height_bytes)
        if winners_bytes is None:
            return []
        result = [winners_bytes[i : i + 32] for i in range(0, 10 * 32, 32)]
        return result if not encode_to_hex else [h.hex() for h in result]

    def put_winners(self, height: int, winners: List[bytes]):
        sub_db = self._db.prefixed_db(WINNERS)
        height_bytes = struct.pack(">I", height)
        winners_bytes = b"".join(winners)
        sub_db.put(height_bytes, winners_bytes)

    def get_highest_winners(self, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        height = self.get_winners_head()
        return [] if height == -1 else self.get_winners(height, encode_to_hex)

    def get_rates(self, height: int) -> Dict[str, float]:
        sub_db = self._db.prefixed_db(RATES)
        height_bytes = struct.pack(">I", height)
        rates_bytes = sub_db.get(height_bytes)
        return None if rates_bytes is None else json.loads(rates_bytes.decode())

    def put_rates(self, height: int, rates: Dict[str, float]) -> None:
        sub_db = self._db.prefixed_db(RATES)
        height_bytes = struct.pack(">I", height)
        rates_bytes = json.dumps(rates, separators=(",", ":")).encode()
        sub_db.put(height_bytes, rates_bytes)
