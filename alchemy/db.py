import json
import plyvel
import os
import struct
from factom_keys.fct import FactoidAddress
from typing import Dict, List, Union


OPR_HEAD = b"OPRHead"
FACTOID_HEAD = b"FactoidHead"
TRANSACTION_HEAD = b"TxHead"
BALANCES = b"Balances"
WINNERS = b"Winners"

BalanceMap = Dict[str, int]


class AlchemyDB:
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

    def get_transaction_head(self) -> int:
        height_bytes = self._db.get(TRANSACTION_HEAD)
        return -1 if height_bytes is None else struct.unpack(">I", height_bytes)[0]

    def put_transaction_head(self, height: int):
        height_bytes = struct.pack(">I", height)
        self._db.put(TRANSACTION_HEAD, height_bytes)

    def get_balances(self, address: Union[bytes, str]) -> Union[None, Dict[str, int]]:
        """Gets a map of balances for the given address.
        :param address: A bytes object of the address RCD hash, or a string of the address in human readable notation
        """
        sub_db = self._db.prefixed_db(BALANCES)
        if type(address) == str:
            address = FactoidAddress(address_string=address).rcd_hash
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
                if k in balances:
                    balances[k] += v
                else:
                    balances[k] = v
            self.put_balances(address, balances)
        else:
            self.put_balances(address, deltas)

    def get_winners(self, height: int, encode_to_hex: bool = False) -> List[bytes]:
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
