from typing import Dict, List, Union


class AlchemyDB:
    def get_sync_head(self) -> int:
        raise NotImplementedError()

    def put_sync_head(self, height: int):
        raise NotImplementedError()

    def get_balances(self, address: Union[bytes, str]) -> Union[None, Dict[str, int]]:
        """Gets a map of balances for the given address.
        :param address: A bytes object of the address RCD hash, or a string of the address in human readable notation
        """
        raise NotImplementedError()

    def put_balances(self, address: bytes, balances: Dict[str, int]):
        raise NotImplementedError()

    def update_balances(self, address: bytes, deltas: Dict[str, int]):
        raise NotImplementedError()

    def get_oracle_block(self, height: int):
        raise NotImplementedError()

    def put_oracle_block(self, height: int, competitors: List[bytes], winners: List[bytes], rates: Dict[str, float]):
        raise NotImplementedError()

    def get_latest_oracle_block(self):
        raise NotImplementedError()

    def get_competitors(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        raise NotImplementedError()

    def get_winners(self, height: int, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        raise NotImplementedError()

    def get_latest_winners(self, encode_to_hex: bool = False) -> Union[List[bytes], List[str]]:
        raise NotImplementedError()

    def get_rates(self, height: int) -> Dict[str, float]:
        raise NotImplementedError()

    def get_latest_rates(self) -> Dict[str, float]:
        raise NotImplementedError()
