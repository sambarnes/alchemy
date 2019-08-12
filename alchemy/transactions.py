import dataclasses
import datetime
import hashlib
import json
from dataclasses import dataclass
from factom import Factomd, FactomWalletd
from factom_keys.ec import ECAddress
from factom_keys.fct import FactoidAddress, FactoidPrivateKey
from typing import Any, Dict, List, Tuple

import alchemy.consts as consts

CHAIN_ID = ""  # TODO: set transactions.CHAIN_ID


@dataclass
class Transaction:
    input: Dict[str, Any] = None
    outputs: List[Dict[str, Any]] = None
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

    def add_output(self, address: FactoidAddress, asset_type: str = None, amount: int = None):
        """
        :param address: The public Factoid address receiving the assets being transacted
        :param asset_type: The pegged asset token ticker to convert to
        :param amount: The amount of `asset_type` tokens being asked for
        :return:
        """
        output = dict()
        if address is not None:
            output["address"] = address.to_string()
        if asset_type is not None:
            output["type"] = asset_type
        if amount is not None:
            output["amount"] = amount
        self.outputs.append(output)

    def to_dict(self):
        tx = {"input": self.input, "outputs": self.outputs}
        if self.metadata is not None:
            tx["metadata"] = self.metadata
        return tx

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        return Transaction(input=d.get("input"), outputs=d.get("outputs"), metadata=d.get("metadata"))

    def is_valid(self) -> bool:
        if type(self.input) != dict:
            return False

        input_address = self.input.get("address")
        if not FactoidAddress.is_valid(input_address):
            return False  # Address must be a valid Factoid address string

        input_type = self.input.get("type")
        if input_type not in consts.ALL_ASSETS:
            return False  # Input type must be a valid pegged asset

        input_amount = self.input.get("amount")
        if input_amount is not None:
            if type(input_amount) != int or input_amount < 0:
                return False  # Input amount must be None or a positive integer

        if type(self.outputs) != list:
            return False
        for output in self.outputs:
            if type(output) != dict:
                return False

            output_address = output.get("address")
            if not FactoidAddress.is_valid(output_address):
                return False

            output_type = output.get("type")
            if output_type is not None:
                if output_type not in consts.ALL_ASSETS:
                    return False  # Not a valid token type
                if output_type != input_type and output_address != input_address:
                    return False  # Conversion Tx. Must output to the same address

            output_amount = output.get("amount")
            if output_amount is None:
                if input_amount is None:
                    return False  # Input amount is None, output amount must not be None
            else:
                if type(output_amount) != int or output_amount < 0:
                    return False  # Output amount must be None or a positive integer
        return True


@dataclass
class TransactionsEntry:
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
        tx_payload = {"transactions": [tx.to_dict() for tx in self._txs]}
        return json.dumps(tx_payload, separators=(",", ":")).encode()


def send(txs_entry: TransactionsEntry, ec_address: ECAddress):
    factomd = Factomd(ec_address=ec_address.to_string())
    walletd = FactomWalletd()
    walletd.new_entry(factomd=factomd, chain_id=CHAIN_ID, ext_ids=txs_entry.external_ids, content=txs_entry.content)
