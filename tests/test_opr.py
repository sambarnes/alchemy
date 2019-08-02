import unittest

from alchemy.opr import OPR


class TestOPR(unittest.TestCase):

    cases = {
        "valid": {
            "should_be_valid": True,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_nonce": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": None,
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_content_not_json": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": "I AM NOT JSON".encode(),
        },
        "bad_content_missing_usd": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_content_extra_asset": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686'
            ',"EXTRA_ASSET":0}}'.encode(),
        },
        "bad_content_miner_id": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":1234,"assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_coinbase_address": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2XXBADLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_height": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":"49","winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_prev_winners": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("8c53fab4989f820bf3f4ced996a055c1d1b17faf569c76c0a3e65ff4ea7babea"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["X",'
            '"BAD", 0],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
        "bad_entry_hash": {
            "should_be_valid": False,
            "entry_hash": bytes.fromhex("FFFFFF"),
            "nonce": b"\x42\x2c\x68",
            "self_reported_difficulty": b"\xff\xff\xf7\xa7\xf2\x5c\xfa\x2a",
            "content": '{"coinbase":"FA2jK2HcLnRdS94dEcU27rF3meoJfpUcZPSinpb7AwQvPRY6RL1Q","dbht":49,"winners":["",'
            '"","","","","","","","",""],"minerid":"prototype","assets":{"PNT":0,"USD":1.0112,"EUR":0.9063,"JPY":11'
            '1.1654,"GBP":0.8338,"CAD":1.337,"CHF":0.9862,"INR":70.8935,"SGD":1.417,"CNY":7.0193,"HKD":7.7231,"KRW"'
            ':1192.4807,"BRL":3.8149,"PHP":51.251,"MXN":19.2589,"XAU":16.3876,"XAG":1394.0085,"XPD":1469.3358,"XPT"'
            ':860.2949,"XBT":9855.9643,"ETH":210.043,"LTC":97.7357,"RVN":0.0425,"XBC":322.7583,"FCT":3.9323,"BNB":2'
            '8.2205,"XLM":0.0819,"ADA":0.0584,"XMR":83.2906,"DASH":107.2641,"ZEC":65.5538,"DCR":28.1686}}'.encode(),
        },
    }

    def test_from_entry(self):
        for name, case in TestOPR.cases.items():
            record = OPR.from_entry(
                entry_hash=case["entry_hash"],
                external_ids=[case["nonce"], case["self_reported_difficulty"]],
                content=case["content"],
            )
            if case["should_be_valid"]:
                self.assertIsNotNone(record, f'Case "{name}"')
            else:
                self.assertIsNone(record, f'Case "{name}"')
