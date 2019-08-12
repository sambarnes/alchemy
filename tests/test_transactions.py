import unittest

from alchemy.transactions import Transaction, TransactionsEntry


class TestTransactions(unittest.TestCase):
    def test_conversions(self):
        good_cases = {
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
        bad_cases = {
            "two separate addresses": {
                "input": {
                    "address": "FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q",
                    "type": "PNT",
                    "amount": 50,
                },
                "outputs": [
                    {"address": "FA1zT4aFpEvcnPqPCigB3fvGu4Q4mTXY22iiuV69DqE1pNhdF2MC", "type": "USD", "amount": 50}
                ],
            }
        }

        for name, case in good_cases.items():
            tx = Transaction.from_dict(case)
            self.assertTrue(tx.is_valid(), f'Case "{name}" should be valid')

        for name, case in bad_cases.items():
            tx = Transaction.from_dict(case)
            self.assertFalse(tx.is_valid(), f'Case "{name}" should be invalid')
