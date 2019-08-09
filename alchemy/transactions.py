import dataclasses
import datetime
import hashlib
import json
from dataclasses import dataclass
from factom import Factomd, FactomWalletd
from factom_keys.ec import ECAddress
from factom_keys.fct import FactoidAddress, FactoidPrivateKey
from typing import Any, Dict, List, Tuple


CHAIN_ID = ""  # TODO: set transactions.CHAIN_ID


@dataclass
class Transaction:
    input: Dict[str, Any]
    outputs: List[Dict[str, Any]]
    metadata: str = None

    def set_input(self, address: FactoidAddress, asset_type: str, amount: int = None):
        """

        :param address: The public Factoid address spending the assets being transacted
        :param asset_type: The pegged asset token ticker to convert from
        :param amount: The amount of `asset_type` tokens being converted
        :return:
        """
        self.input = {"address": address.to_string(), "type": asset_type}
        if amount is not None:
            self.input["amount"] = amount

    def add_output(self, address: FactoidAddress, asset_type: str, amount: int = None):
        """

        :param address: The public Factoid address receiving the assets being transacted
        :param asset_type: The pegged asset token ticker to convert to
        :param amount: The amount of `asset_type` tokens being asked for
        :return:
        """
        output = {"address": address.to_string(), "type": asset_type}
        if amount is not None:
            output["amount"] = amount
        self.outputs.append(output)

    def to_dict(self):
        tx = {"input": self.input, "output": self.outputs}
        if self.metadata is not None:
            tx["metadata"] = self.metadata
        return tx


@dataclass
class TransactionEntry:
    timestamp: str = str(datetime.datetime.utcnow().timestamp())

    _txs: List[Transaction] = dataclasses.field(init=False)
    _signer_keys: List[FactoidPrivateKey] = dataclasses.field(init=False)

    def add_transaction(self, tx: Transaction) -> None:
        self._txs.append(tx)

    def add_signer(self, key: FactoidPrivateKey) -> None:
        self._signer_keys.append(key)

    @property
    def external_ids(self):
        """
        Using the given Factoid private key, add a signature to the transaction entry as defined by:
        https://github.com/Factom-Asset-Tokens/FAT/blob/master/fatips/103.md#salting-hashing-and-signing
        """
        ids = [self.timestamp.encode()]
        content = self.content
        for i, key in enumerate(self._signer_keys):
            rcd = b"\x01" + key.get_factoid_address().key_bytes
            ids.append(rcd)

            message = bytearray()
            message.extend(str(i).encode())
            message.extend(self.timestamp.encode())
            message.extend(CHAIN_ID)
            message.extend(content)
            message_hash = hashlib.sha512(message).digest()
            signature = key.sign(message_hash)
            ids.append(signature)

        return ids

    @property
    def content(self):
        tx_payload = {"transactions": [tx.to_dict() for tx in self.txs]}
        return json.dumps(tx_payload, separators=(",", ":")).encode()


def send(tx_entry: TransactionEntry, ec_address: ECAddress):
    factomd = Factomd(ec_address=ec_address.to_string())
    walletd = FactomWalletd()
    walletd.new_entry(factomd=factomd, chain_id=CHAIN_ID, ext_ids=tx_entry.external_ids, content=tx_entry.content)
