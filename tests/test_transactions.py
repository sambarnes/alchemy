import unittest

import numpy as np
from factom_keys.fct import FactoidAddress, FactoidPrivateKey

from alchemy.transactions import Transaction, TransactionEntry


class TestTransactions(unittest.TestCase):
    def test_to_dict(self):
        tx = Transaction()
        tx.set_input(
            address=FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC"),
            asset_type="PNT",
            amount=50,
        )
        tx.add_output(
            address=FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC"), amount=50
        )

        expected_dict = {
            "input": {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 50},
            "outputs": [{"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "amount": 50}],
        }
        self.assertEqual(tx.to_dict(), expected_dict)

    def test_transactions_is_valid(self):
        valid_cases = {
            "single input, single output": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 50}
                ],
            },
            "single input, multiple outputs": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 25},
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 25},
                ],
            },
        }
        for name, case in valid_cases.items():
            tx = Transaction.from_dict(case)
            self.assertTrue(tx.is_valid(), f'Case "{name}" should be valid')

        invalid_cases = {
            # Related to bad inputs
            "input not a dict": {
                "input": None,
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD", "amount": 50}
                ],
            },
            "bad input address": {
                "input": {
                    "address": "FAXXXHcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "PNT", "amount": 50}
                ],
            },
            "no input address": {
                "input": {"type": "PNT", "amount": 50},
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "PNT", "amount": 50}
                ],
            },
            "bad input ticker": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "BAD",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 50}
                ],
            },
            "no input amount": {
                "input": {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "PNT"},
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "PNT", "amount": 50}
                ],
            },
            "negative input": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": -1,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 50}
                ],
            },
            # Related to bad outputs
            "outputs not an array": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": None,
            },
            "bad output element": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 25},
                    None,
                ],
            },
            "bad output address": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "XXXXT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "USD", "amount": 50}
                ],
            },
            "bad output ticker": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "BAD", "amount": 50}
                ],
            },
            "negative output": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": -1}
                ],
            },
        }
        for name, case in invalid_cases.items():
            tx = Transaction.from_dict(case)
            self.assertFalse(tx.is_valid(), f'Case "{name}" should be invalid')

    def test_conversions_is_valid(self):
        valid_cases = {
            "one input, one output": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD", "amount": 50}
                ],
            },
            "one input, multiple outputs": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD", "amount": 50},
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "FCT", "amount": 50},
                ],
            },
            "no output amount": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [{"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD"}],
            },
        }
        for name, case in valid_cases.items():
            tx = Transaction.from_dict(case)
            self.assertTrue(tx.is_valid(), f'Case "{name}" should be valid')

        invalid_cases = {
            "no amounts": {
                "input": {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "PNT"},
                "outputs": [{"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD"}],
            },
            "two separate addresses": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "USD", "amount": 50}
                ],
            },
        }
        for name, case in invalid_cases.items():
            tx = Transaction.from_dict(case)
            self.assertFalse(tx.is_valid(), f'Case "{name}" should be invalid')

    def test_get_deltas(self):
        rates = {
            "PNT": 0,
            "USD": 1,
            "EUR": 0.8949,
            "JPY": 106.4114,
            "GBP": 0.8292,
            "CAD": 1.3223,
            "CHF": 0.9759,
            "INR": 70.9458,
            "SGD": 1.3848,
            "CNY": 7.0453,
            "HKD": 7.8454,
            "KRW": 1213.2303,
            "BRL": 3.9637,
            "PHP": 52.2349,
            "MXN": 19.4161,
            "XAU": 1502.2909,
            "XAG": 16.9726,
            "XPD": 1448.1,
            "XPT": 850.8248,
            "XBT": 10607.0505,
            "ETH": 207.9157,
            "LTC": 85.4049,
            "RVN": 0.036,
            "XBC": 353.4228,
            "FCT": 3.2319,
            "BNB": 28.6258,
            "XLM": 0.0738,
            "ADA": 0.053,
            "XMR": 84.5382,
            "DASH": 102.0781,
            "ZEC": 56.0201,
            "DCR": 25.5828,
        }

        valid_cases = {
            "single output": {
                "tx": {
                    "input": {
                        "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                        "type": "PNT",
                        "amount": 50,
                    },
                    "outputs": [
                        {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "PNT", "amount": 50}
                    ],
                },
                "expected_deltas": {
                    FactoidAddress(address_string="FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q").rcd_hash: {
                        "PNT": -50
                    },
                    FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC").rcd_hash: {
                        "PNT": 50
                    },
                },
            },
            "multiple outputs": {
                "tx": {
                    "input": {
                        "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                        "type": "PNT",
                        "amount": 50,
                    },
                    "outputs": [
                        {
                            "address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC",
                            "type": "PNT",
                            "amount": 25,
                        },
                        {
                            "address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC",
                            "type": "PNT",
                            "amount": 25,
                        },
                    ],
                },
                "expected_deltas": {
                    FactoidAddress(address_string="FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q").rcd_hash: {
                        "PNT": -50
                    },
                    FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC").rcd_hash: {
                        "PNT": 50
                    },
                },
            },
            "FCT -> XBT: no output amount": {
                "tx": {
                    "input": {
                        "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                        "type": "FCT",
                        "amount": 50e8,
                    },
                    "outputs": [{"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "XBT"}],
                },
                "expected_deltas": {
                    FactoidAddress(address_string="FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q").rcd_hash: {
                        "FCT": -50e8
                    },
                    FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC").rcd_hash: {
                        "XBT": np.trunc(50e8 * rates["FCT"] / rates["XBT"])
                    },
                },
            },
            "FCT -> XBT: with output amount": {
                "tx": {
                    "input": {
                        "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                        "type": "FCT",
                        "amount": 50e8,
                    },
                    "outputs": [
                        {
                            "address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC",
                            "type": "XBT",
                            "amount": 1e6,
                        }
                    ],
                },
                "expected_deltas": {
                    FactoidAddress(address_string="FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q").rcd_hash: {
                        "FCT": -np.trunc(1e6 * rates["XBT"] / rates["FCT"])
                    },
                    FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC").rcd_hash: {
                        "XBT": 1e6
                    },
                },
            },
        }
        for name, case in valid_cases.items():
            tx = Transaction.from_dict(case["tx"])
            deltas = tx.get_deltas(rates)
            self.assertEqual(deltas, case["expected_deltas"], f'Case "{name}": \n{deltas}\n{case["expected_deltas"]}')


class TestTransactionEntry(unittest.TestCase):
    def test_valid_sign_and_verify(self):
        # Signer: FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q
        input_signer = FactoidPrivateKey(key_string="Fs3E9gV6DXsYzf7Fqx1fVBQPQXV695eP3k5XbmHEZVRLkMdD9qCK")
        tx = Transaction()
        tx.set_input(address=input_signer.get_factoid_address(), asset_type="PNT", amount=50)
        tx.add_output(
            address=FactoidAddress(address_string="FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC"), amount=50
        )
        tx_entry = TransactionEntry()
        tx_entry.add_transaction(tx)
        tx_entry.add_signer(input_signer)
        external_ids, content = tx_entry.sign()
        tx_entry_from_entry = TransactionEntry.from_entry(external_ids, content)
        self.assertIsNotNone(tx_entry_from_entry)

    def test_valid_sign_and_verify_multiple_txs(self):
        tx_entry = TransactionEntry()

        # FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q
        input_signer = FactoidPrivateKey(key_string="Fs3E9gV6DXsYzf7Fqx1fVBQPQXV695eP3k5XbmHEZVRLkMdD9qCK")
        tx = Transaction()
        tx.set_input(address=input_signer.get_factoid_address(), asset_type="PNT", amount=50)
        tx.add_output(address=input_signer.get_factoid_address(), amount=50)
        tx_entry.add_transaction(tx)
        tx_entry.add_signer(input_signer)

        # FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC
        input_signer = FactoidPrivateKey(key_string="Fs1KWJrpLdfucvmYwN2nWrwepLn8ercpMbzXshd1g8zyhKXLVLWj")
        tx = Transaction()
        tx.set_input(address=input_signer.get_factoid_address(), asset_type="PNT", amount=50)
        tx.add_output(address=input_signer.get_factoid_address(), amount=50)
        tx_entry.add_transaction(tx)
        tx_entry.add_signer(input_signer)

        external_ids, content = tx_entry.sign()
        tx_entry_from_entry = TransactionEntry.from_entry(external_ids, content)
        self.assertIsNotNone(tx_entry_from_entry)

    def test_missing_signature(self):
        tx_entry = TransactionEntry()

        # FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q
        input_signer = FactoidPrivateKey(key_string="Fs3E9gV6DXsYzf7Fqx1fVBQPQXV695eP3k5XbmHEZVRLkMdD9qCK")
        tx = Transaction()
        tx.set_input(address=input_signer.get_factoid_address(), asset_type="PNT", amount=50)
        tx.add_output(address=input_signer.get_factoid_address(), amount=50)
        tx_entry.add_transaction(tx)
        tx_entry.add_signer(input_signer)

        # FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC
        input_signer = FactoidPrivateKey(key_string="Fs1KWJrpLdfucvmYwN2nWrwepLn8ercpMbzXshd1g8zyhKXLVLWj")
        tx = Transaction()
        tx.set_input(address=input_signer.get_factoid_address(), asset_type="PNT", amount=50)
        tx.add_output(address=input_signer.get_factoid_address(), amount=50)
        tx_entry.add_transaction(tx)
        # tx_entry.add_signer(input_signer)  DELIBERATELY MISSING THIS

        external_ids, content = tx_entry.sign()
        tx_entry_from_entry = TransactionEntry.from_entry(external_ids, content)
        self.assertIsNone(tx_entry_from_entry)
