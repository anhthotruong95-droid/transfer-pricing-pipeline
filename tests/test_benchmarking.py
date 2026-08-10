"""
test_benchmarking.py
-------------------------
Unit tests for tp_pipeline.benchmarking: operating margin / full cost
markup calculations and the Within/Out of Range classification.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tp_pipeline.benchmarking import (calculate_operating_margin_pct, calculate_full_cost_markup_pct,
                                       classify_against_benchmark)


def test_operating_margin_basic():
    result = calculate_operating_margin_pct(revenue=100, cogs=70, sga=10, rd=0, other_opex=5)
    assert result == 15.0, f"Expected 15.0, got {result!r}"


def test_operating_margin_zero_revenue():
    result = calculate_operating_margin_pct(revenue=0, cogs=10, sga=5, rd=0, other_opex=0)
    assert result == 0.0, f"Expected 0.0, got {result!r}"


def test_full_cost_markup_basic():
    result = calculate_full_cost_markup_pct(revenue=108, cogs=80, sga=10, rd=5, other_opex=5)
    assert result == 8.0, f"Expected 8.0, got {result!r}"


def test_classify_within_range():
    benchmark = {"lower_quartile": 2.0, "upper_quartile": 5.0}
    result = classify_against_benchmark(3.5, benchmark)
    assert result == "Within Range", f"Expected 'Within Range', got {result!r}"


def test_classify_out_of_range():
    benchmark = {"lower_quartile": 2.0, "upper_quartile": 5.0}
    result = classify_against_benchmark(1.0, benchmark)
    assert result == "Out of Range", f"Expected 'Out of Range', got {result!r}"


def test_classify_no_benchmark():
    result = classify_against_benchmark(3.5, None)
    assert result == "No benchmark available", f"Expected 'No benchmark available', got {result!r}"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASSED:", t.__name__)
    print(f"\n{len(tests)} tests passed.")