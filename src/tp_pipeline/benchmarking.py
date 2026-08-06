"""
benchmarking.py
------------------
Calculates the financial metrics used in Transfer Pricing benchmarking
(operating margin, full cost mark-up) and classifies each result as
Within Range or Out of Range vs. a benchmark study's interquartile range.
"""

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
    print(" Operating Margin %:", calculate_operating_margin_pct(100, 20, 10, 5, 5))
    print(" Full Cost Markup %:", calculate_full_cost_markup_pct(100, 20, 10, 5, 5))
    print(classify_against_benchmark(0.2, {"lower_quartile": 0.1, "upper_quartile": 0.3}))
    print(classify_against_benchmark(0.6, {"lower_quartile": 0.1, "upper_quartile": 0.3}))