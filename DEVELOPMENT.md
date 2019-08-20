# Development

## Grading
I am in the process of refactoring the grading of OPRs to be a pluggable class interface. This should allow more people to quickly iterate on their ideas for grading, and compare them against other implementations.

The entrance point to the grader is located in [`alchemy/grading/grading.py`](https://github.com/sambarnes/alchemy/blob/master/alchemy/grading/grading.py#L25). To use another grading implementation, just swap out the instantiation of the StockGrader for the custom one.

The only requirement for custom grading implementations is that they extend [`BaseGrader`](https://github.com/sambarnes/alchemy/blob/master/alchemy/grading/graders/base.py) and implement the `grade_records()` function where:

- inputs:
    - `previous_winners: List[str]` - previous winning short hashes (first 8 bytes of hex for each entry hash)
    - `records: List[OPR]` - all records submitted within the block
- outputs:
    - `Dict[str, float]` - winning asset prices for the block
    - `List[OPR]` - the top 50 records sorted by grade
    - `List[OPR]` - the top 50 records sorted by difficulty

For an example, see the `StockGrader` implementation [here](https://github.com/sambarnes/alchemy/blob/master/alchemy/grading/graders/stock.py).
