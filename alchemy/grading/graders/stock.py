import numpy as np
from typing import List

import alchemy.consts as consts
import alchemy.grading.graders as graders
from alchemy.opr import OPR, AssetEstimates


class StockGrader(graders.BaseGrader):
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

        # TODO: opr.RemoveDuplicateSubmissions().
        #       Technically not needed, but should match reference implementation

        # Then calculate grade for each record in the top 50 and sort
        graded_records = eligible_records
        for i in range(len(graded_records), -1, -1):
            if i < 10:
                break
            averages = StockGrader.average_estimates(graded_records[:i])
            for j in range(i):
                graded_records[j].grade = StockGrader.calculate_record_grade(
                    record_estimates=graded_records[j].asset_estimates, averages=averages
                )
            graded_records[:i] = sorted(graded_records[:i], key=lambda x: x.self_reported_difficulty, reverse=True)
            graded_records[:i] = sorted(graded_records[:i], key=lambda x: x.grade)

        # Return Tuple(winning prices for the block, top 50 by grade, top 50 by difficulty)
        return graded_records[0].asset_estimates, graded_records, eligible_records

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

    @classmethod
    def average_estimates(cls, records: List[OPR]) -> AssetEstimates:
        """Computes the average answer for the price of each token reported"""
        averages: AssetEstimates = {k: np.float64(0) for k in consts.ASSET_GRADING_ORDER}
        # Sum up all the prices
        for record in records:
            for k, v in record.asset_estimates.items():
                # Make sure no OPR has negative values for assets.  Simply treat all values as positive.
                averages[k] += np.float64(abs(v))
        # Then divide the prices by the number of OraclePriceRecord records.  Two steps is actually faster
        # than doing everything in one loop (one divide for every asset rather than one divide
        # for every asset * number of OraclePriceRecords)  There is also a little bit of a precision advantage
        # with the two loops (fewer divisions usually does help with precision) but that isn't likely to be
        # interesting here.
        n_records = np.float64(len(records))
        averages = {k: v / n_records for k, v in averages.items()}
        return averages

    @classmethod
    def calculate_record_grade(cls, record_estimates: AssetEstimates, averages: AssetEstimates) -> np.float64:
        """Given a map of price estimates and a second map of average estimates, calculate and return a grade
        where `grade = Σ(asset_difference^4)` over all assets in the set
        """
        grade = np.float64(0)
        for k in consts.ASSET_GRADING_ORDER:
            v = record_estimates.get(k)
            if averages[k] > 0:
                d = (v - averages[k]) / averages[k]
                grade += np.float64(d * d * d * d)
        return grade
