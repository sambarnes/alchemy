import unittest

from alchemy.transactions import Transaction, TransactionsEntry


class TestTransactions(unittest.TestCase):
    def test_is_valid(self):
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


class TestConversions(unittest.TestCase):
    def test_is_valid(self):
        valid_cases = {
            "PNT -> pUSD": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD", "amount": 50}
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
            "no input amount": {
                "input": {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "PNT"},
                "outputs": [
                    {"address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q", "type": "USD", "amount": 50}
                ],
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
