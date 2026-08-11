"""
benchmarking.py
------------------
Classifies a Transfer Pricing metric (Operating Margin %, Full Cost
Mark-up %) as Within Range or Out of Range vs. a benchmark study's
interquartile range.
"""
from typing import Optional


def classify_against_benchmark(value: float, benchmark: Optional[dict]) -> str:
    """Classifies a metric as Within Range or Out of Range vs. a benchmark's interquartile range."""
    if benchmark is None:
        return "No benchmark available"
    lq, uq = benchmark["lower_quartile"], benchmark["upper_quartile"]
    if lq <= value <= uq:
        return "Within Range"
    else:
        return "Out of Range"


if __name__ == "__main__":
    print(classify_against_benchmark(0.2, {"lower_quartile": 0.1, "upper_quartile": 0.3}))
    print(classify_against_benchmark(0.6, {"lower_quartile": 0.1, "upper_quartile": 0.3}))