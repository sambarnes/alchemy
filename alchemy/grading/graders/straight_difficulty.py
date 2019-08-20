from typing import List

import alchemy.grading.graders as graders
from alchemy.opr import OPR


class StraightDifficultyGrader(graders.BaseGrader):
    """
    The current reference implementation for PegNet grading.

    Known issues:
    - encourages pricing centralization: miners have the incentive to be precise relative to other miners, rather than
      an incentive to provide accurate prices
    - TODO: write more...
    """

    def grade_records(self, previous_winners: List[str], records: List[OPR]):
        if len(records) < 10:
            return None, None, None  # Not enough sane records to grade

        # Get top 50 honest submissions by difficulty
        eligible_records = self.filter_top_50(previous_winners, records)
        if len(eligible_records) < 10:
            return None, None, None  # Must have at least 10 eligible submissions to grade them

        # Winning prices is the average of the top 50
        winning_rates = graders.StockGrader.average_estimates(eligible_records)

        # Return Tuple(winning prices for the block, top 50 by grade, top 50 by difficulty)
        return winning_rates, eligible_records, eligible_records

    def filter_top_50(self, previous_winners: List[str], records: List[OPR]) -> List[OPR]:
        """Returns the top 50 most difficult submissions that are honest and also have """
        records.sort(key=lambda x: x.self_reported_difficulty, reverse=True)
        valid_records: List[OPR] = []
        for o in records:
            difficulty = self.lxr.h(o.opr_hash + o.nonce)[:8]
            if difficulty != o.self_reported_difficulty:
                print(
                    f"Dishonest OPR difficulty: e_hash={o.entry_hash.hex()}, observed={difficulty.hex()}, reported={o.self_reported_difficulty.hex()}"
                )
                continue
            if o.prev_winners != previous_winners:
                continue
            valid_records.append(o)
            if 50 <= len(valid_records):
                break  # Found max number of honest submissions, go grade them
        return valid_records
