import json
import plyvel
import os
import struct
from factom_keys.fct import FactoidAddress
from typing import Dict, List, Union

from alchemy.database import AlchemyDB


SYNC_HEAD = b"SyncHead"
ORACLE_BLOCK_HEAD = b"Head"
BALANCES = b"Balances"
WINNERS = b"Winners"
RATES = b"Rates"
COMPETITORS = b"Competitors"


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

    def get_oracle_block(self, height: int):
        return {
            "competitors": self.get_competitors(height, encode_to_hex=False),
            "winners": self.get_winners(height, encode_to_hex=False),
            "rates": self.get_rates(height),
        }

    def put_oracle_block(self, height: int, competitors: List[bytes], winners: List[bytes], rates: Dict[str, float]):
        self.put_winners(height, winners)
        self.put_competitors(height, competitors)
        self.put_rates(height, rates)
        # Check if we need to update the block head
        old_block_head = self.get_latest_oracle_block()
        if old_block_head < height:
            height_bytes = struct.pack(">I", height)
            self._db.put(ORACLE_BLOCK_HEAD, height_bytes)

    def get_latest_oracle_block(self) -> int:
        old_block_head_bytes = self._db.get(ORACLE_BLOCK_HEAD)
        return -1 if old_block_head_bytes is None else struct.unpack(">I", old_block_head_bytes)[0]

    def get_competitors(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        sub_db = self._db.prefixed_db(COMPETITORS)
        height_bytes = struct.pack(">I", height)
        competitors_bytes = sub_db.get(height_bytes)
        if competitors_bytes is None:
            return []
        result = [competitors_bytes[i : i + 32] for i in range(0, 10 * 32, 32)]
        return result if not encode_to_hex else [h.hex() for h in result]

    def put_competitors(self, height: int, competitors: List[bytes]):
        sub_db = self._db.prefixed_db(COMPETITORS)
        height_bytes = struct.pack(">I", height)
        competitors_bytes = b"".join(competitors)
        sub_db.put(height_bytes, competitors_bytes)

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

    def get_latest_winners(self, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        height = self.get_latest_oracle_block()
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

    def get_latest_rates(self) -> Dict[str, float]:
        height = self.get_latest_oracle_block()
        return {} if height == -1 else self.get_rates(height)
