from google.cloud import datastore
from factom_keys.fct import FactoidAddress
from typing import Dict, List, Union

from alchemy.database import AlchemyDB

SYNCING = "Syncing"
ACCOUNT = "Account"
BLOCK = "Block"


class AlchemyCloudDB(AlchemyDB):
    def __init__(self):
        self._db = datastore.Client(namespace="Alchemy")

    def get_sync_head(self) -> int:
        entity_key = self._db.key(SYNCING, SYNCING)
        entity = self._db.get(entity_key)
        return -1 if entity is None else entity.get("height", -1)

    def put_sync_head(self, height: int):
        entity_key = self._db.key(SYNCING, SYNCING)
        entity = datastore.Entity(key=entity_key)
        entity.update({"height": height})
        self._db.put(entity)

    def get_balances(self, address: Union[bytes, str]) -> Union[None, Dict[str, int]]:
        address_string = address if type(address) == str else FactoidAddress(rcd_hash=address).to_string()
        entity_key = self._db.key(ACCOUNT, address_string)
        return self._db.get(entity_key)

    def put_balances(self, address: Union[bytes, str], balances: Dict[str, int]):
        address_string = address if type(address) == str else FactoidAddress(rcd_hash=address).to_string()
        entity_key = self._db.key(ACCOUNT, address_string)
        entity = datastore.Entity(key=entity_key)
        entity.update(balances)
        self._db.put(entity)

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

    def get_oracle_block(self, height: int, encode_to_hex: bool = False):
        query = self._db.query(kind=BLOCK)
        query.add_filter("height", "=", height)
        blocks = list(query.fetch(limit=1))
        if len(blocks) == 0:
            return None
        block = blocks[0]
        if encode_to_hex:
            block["competitors"] = [x.hex() for x in block["competitors"]]
            block["winners"] = [x.hex() for x in block["winners"]]
        return block

    def put_oracle_block(self, height: int, competitors: List[bytes], winners: List[bytes], rates: Dict[str, float]):
        entity_key = self._db.key(BLOCK)
        entity = datastore.Entity(key=entity_key)
        entity.update({"height": height, "competitors": competitors, "winners": winners, "rates": rates})
        self._db.put(entity)

    def get_latest_oracle_block(self, encode_to_hex: bool = False):
        query = self._db.query(kind=BLOCK)
        query.order = ["-height"]
        blocks = list(query.fetch(limit=1))
        if len(blocks) == 0:
            return None
        block = blocks[0]
        if encode_to_hex:
            block["competitors"] = [x.hex() for x in block["competitors"]]
            block["winners"] = [x.hex() for x in block["winners"]]
        return block

    def get_competitors(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        block = self.get_oracle_block(height)
        if block is None:
            return None
        competitors = block.get("competitors", [])
        return competitors if not encode_to_hex else [x.hex() for x in competitors]

    def get_winners(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        block = self.get_oracle_block(height)
        if block is None:
            return None
        winners = block.get("winners", [])
        return winners if not encode_to_hex else [x.hex() for x in winners]

    def get_latest_winners(self, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        block = self.get_latest_oracle_block()
        winners = [] if block is None else block.get("winners", [])
        return winners if not encode_to_hex else [x.hex() for x in winners]

    def get_rates(self, height: int) -> Dict[str, float]:
        block = self.get_oracle_block(height)
        if block is None:
            return None
        return block.get("rates")

    def get_latest_rates(self) -> Dict[str, float]:
        block = self.get_latest_oracle_block()
        if block is None:
            return None
        return block.get("rates")
