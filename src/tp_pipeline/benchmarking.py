"""
benchmarking.py
------------------
Calculates the financial metrics used in Transfer Pricing benchmarking
(operating margin, full cost mark-up, royalty rate) and classifies each
result against a benchmark study's interquartile range.
"""

# ------------------------------------------------------------ Profit Level Indicator
from typing import Optional

def calculate_operating_margin_pct(revenue: float, cogs: float, sga: float, rd: float, other_opex: float) -> float:
    """Operating Margin % = Operating Profit / Revenue x 100 - used for Distribution."""
    if revenue == 0:
        return 0.0
    operating_profit = revenue - cogs - sga - rd - other_opex
    return round(operating_profit / revenue * 100, 2)


def calculate_full_cost_markup_pct(revenue: float, cogs: float, sga: float, rd: float, other_opex: float) -> float:
    """Full Cost Markup % = (Revenue - Full Cost) / Full Cost x 100 - used for Contract Manufacturing."""
    full_cost = cogs + sga + rd + other_opex
    if full_cost == 0:
        return 0.0
    return round((revenue - full_cost) / full_cost * 100, 2)


def calculate_royalty_rate_pct(royalty_paid: float, net_sales: float) -> float:
    """Royalty Rate % = Royalty Paid / Net Sales x 100 - used for IP / Licensing."""
    if net_sales == 0:
        return 0.0
    return round(royalty_paid / net_sales * 100, 2)


# ------------------------------------------------------------------- Benchmark
def classify_against_benchmark(value: float, benchmark: Optional[dict]):
    """Classifies a metric against a benchmark's min/lower quartile/upper quartile/max."""
    if benchmark is None:
        return "No benchmark available"

    benchmark_min, lq, uq, benchmark_max = (
        benchmark["benchmark_min"], benchmark["benchmark_lower_quartile"],
        benchmark["benchmark_upper_quartile"], benchmark["benchmark_max"]
    )

    if value >= lq and value <= uq:
        return f"The PLI of {value} is WITHIN the Interquartile Range of {lq} and {uq}"

    elif value < lq and value < benchmark_min:
        return f"The PLI of {value} is OUTSIDE the Interquartile Range of {lq} and {uq} and OUTSIDE the Benchmark Range"

    elif value > uq and value > benchmark_max:
        return f"The PLI of {value} is OUTSIDE the Interquartile Range of {lq} and {uq} and OUTSIDE the Benchmark Range"

    else:
        return f"The PLI of {value} is OUTSIDE the Interquartile Range of {lq} and {uq} and WITHIN the Benchmark Range"


# ------------------------------------------------------------------- Output
if __name__ == "__main__":
    print(" Operating Margin %:", calculate_operating_margin_pct(100, 20, 10, 5, 5))
    print(" Full Cost Markup %:", calculate_full_cost_markup_pct(100, 20, 10, 5, 5))
    print(" Royalty Rate %:", calculate_royalty_rate_pct(10, 100))
    print(classify_against_benchmark(0.2, {"benchmark_lower_quartile": 0.1, "benchmark_upper_quartile": 0.3, "benchmark_min": 0.05, "benchmark_max": 0.5}))
    print(classify_against_benchmark(0.02, {"benchmark_lower_quartile": 0.1, "benchmark_upper_quartile": 0.3, "benchmark_min": 0.05, "benchmark_max": 0.5}))
    print(classify_against_benchmark(0.6, {"benchmark_lower_quartile": 0.1, "benchmark_upper_quartile": 0.3, "benchmark_min": 0.05, "benchmark_max": 0.5}))
    print(classify_against_benchmark(0.4, {"benchmark_lower_quartile": 0.1, "benchmark_upper_quartile": 0.3, "benchmark_min": 0.05, "benchmark_max": 0.5}))