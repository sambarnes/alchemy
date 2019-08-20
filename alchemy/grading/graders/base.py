import pylxr
from dataclasses import dataclass
from typing import List

from alchemy.opr import OPR


@dataclass
class BaseGrader:
    lxr: pylxr.LXR

    def grade_records(self, previous_winners: List[str], records: List[OPR]):
        """
        Given a list of previous winners (first 8 bytes of entry hashes in hex), grade all records
        and return:
        - a dict of winning asset prices for the block
        - a list of the top 50 records sorted by grade
        - a list of the top 50 records sorted by difficulty
        """
        raise NotImplementedError("All graders must implement the grade_records function")
