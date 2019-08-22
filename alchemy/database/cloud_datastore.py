from google.cloud import datastore
from factom_keys.fct import FactoidAddress
from typing import Dict, List, Union


SYNCING = "Syncing"
ACCOUNT = "Account"
BLOCK = "Block"


class AlchemyCloudDB:
    def __init__(self):
        self._db = datastore.Client(namespace="Alchemy")

    def get_sync_head(self) -> int:
        entity_key = self._db.key(SYNCING, SYNCING)
        return self._db.get(entity_key)

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
        raise NotImplementedError()

    def get_block(self, height: int):
        entity_key = self._db.key(BLOCK, height)
        return self._db.get(entity_key)

    def put_block(self, height: int, competitors: List[bytes], winners: List[bytes], rates: Dict[str, float]):
        entity_key = self._db.key(BLOCK, height)
        entity = datastore.Entity(key=entity_key)
        entity.update({
            "competitors": [x.hex() for x in competitors],
            "winners": [x.hex() for x in winners],
            "rates": rates,
        })
        self._db.put(entity)

    def get_winners_head(self) -> int:
        raise NotImplementedError()

    def put_winners_head(self, height: int):
        raise NotImplementedError()

    def get_winners(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        raise NotImplementedError()

    def put_winners(self, height: int, winners: List[bytes]):
        raise NotImplementedError()

    def get_highest_winners(self, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        raise NotImplementedError()

    def get_rates(self, height: int) -> Dict[str, float]:
        raise NotImplementedError()

    def put_rates(self, height: int, rates: Dict[str, float]) -> None:
        raise NotImplementedError()
