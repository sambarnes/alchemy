import dataclasses
import datetime
import hashlib
import json
from dataclasses import dataclass
from factom import Factomd, FactomWalletd
from factom_keys.ec import ECAddress
from factom_keys.fct import FactoidAddress, FactoidPrivateKey
from typing import Any, Dict, List, Set, Tuple

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
        if self.outputs is None:
            self.outputs = []
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
        """
        Returns True if the structure of the transaction is sane and able to be executed.
        Does not take balances or conversion rates into account
        """
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
class TransactionEntry:
    timestamp: str = str(datetime.datetime.utcnow().timestamp())

    _txs: List[Transaction] = dataclasses.field(init=False, default_factory=list)
    _signer_keys: List[FactoidPrivateKey] = dataclasses.field(init=False, default_factory=list)

    def add_transaction(self, tx: Transaction) -> None:
        self._txs.append(tx)

    def add_signer(self, key: FactoidPrivateKey) -> None:
        self._signer_keys.append(key)

    def sign(self) -> Tuple[List[bytes], bytes]:
        """
        Sign the object using all private keys added to this object. Signature scheme is detailed here:
        https://github.com/Factom-Asset-Tokens/FAT/blob/master/fatips/103.md#salting-hashing-and-signing

        :return: A tuple containing the list of external ids, then the content (all as bytes)
        """
        tx_payload = {"transactions": [tx.to_dict() for tx in self._txs]}
        content = json.dumps(tx_payload, separators=(",", ":")).encode()

        external_ids = [self.timestamp.encode()]
        for i, key in enumerate(self._signer_keys):
            rcd = b"\x01" + key.get_factoid_address().key_bytes
            external_ids.append(rcd)

            message = bytearray()
            message.extend(str(i).encode())
            message.extend(self.timestamp.encode())
            message.extend(CHAIN_ID)
            message.extend(content)
            message_hash = hashlib.sha512(message).digest()
            signature = key.sign(message_hash)
            external_ids.append(signature)

        return external_ids, content

    @classmethod
    def from_entry(cls, external_ids: List[bytes], content: bytes):
        """
        Parses an entry (the external_ids and content) and tries to construct a TransactionEntry.
        If it does not have the proper structure or all required signatures to cover inputs, None will be returned.
        """
        if len(external_ids) < 3 or len(external_ids) % 2 != 1:
            return None  # Number of external ids = 1 + 2 * N, where N is number of signatures >= 1

        timestamp = external_ids[0]

        # Gather all (public key, signature) pairs from the external ids
        full_signatures = external_ids[1:]
        observed_signatures: List[Tuple[FactoidAddress, bytes]] = []
        observed_signers: Set[str] = set()
        for i, rcd in enumerate(full_signatures[::2]):
            signature = full_signatures[2 * i + 1]
            if len(rcd) != 33 or len(signature) != 64:
                return None
            address_bytes = rcd[1:]
            address = FactoidAddress(key_bytes=address_bytes)
            observed_signatures.append((address, signature))
            observed_signers.add(address.to_string())

        # Check that the content field has a valid json with a "transactions" list
        try:
            tx_payload = json.loads(content.decode())
        except ValueError:
            return None
        if "transactions" not in tx_payload:
            return None
        tx_list = tx_payload["transactions"]
        if type(tx_list) != list:
            return None

        # Check that all included inputs are valid and collect the keys we need to have signatures for
        e = TransactionEntry(timestamp=timestamp.decode())
        for tx_dict in tx_list:
            if type(tx_dict) != dict:
                return None
            tx = Transaction(
                input=tx_dict.get("input"), outputs=tx_dict.get("outputs"), metadata=tx_dict.get("metadata")
            )
            if not tx.is_valid():
                return None
            e.add_transaction(tx)
            if tx.input["address"] not in observed_signers:
                return None  # Missing this input signer, not a valid entry

        # Finally check all the signatures
        for i, full_signature in enumerate(observed_signatures):
            key, signature = full_signature

            message = bytearray()
            message.extend(str(i).encode())
            message.extend(timestamp)
            message.extend(CHAIN_ID)
            message.extend(content)
            message_hash = hashlib.sha512(message).digest()
            if not key.verify(signature, message_hash):
                return None

        return e


def send(tx_entry: TransactionEntry, ec_address: ECAddress):
    factomd = Factomd(ec_address=ec_address.to_string())
    walletd = FactomWalletd()
    external_ids, content = tx_entry.sign()
    walletd.new_entry(factomd=factomd, chain_id=CHAIN_ID, ext_ids=external_ids, content=content)
