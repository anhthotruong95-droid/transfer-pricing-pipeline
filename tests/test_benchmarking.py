import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tp_pipeline.benchmarking import (calculate_operating_margin_pct, calculate_full_cost_markup_pct,
                                       classify_against_benchmark)


def test_operating_margin_basic():
    assert calculate_operating_margin_pct(revenue=100, cogs=70, sga=10, rd=0, other_opex=5) == 15.0


def test_operating_margin_zero_revenue():
    assert calculate_operating_margin_pct(revenue=0, cogs=10, sga=5, rd=0, other_opex=0) == 0.0


def test_full_cost_markup_basic():
    assert calculate_full_cost_markup_pct(revenue=108, cogs=80, sga=10, rd=5, other_opex=5) == 8.0


def test_classify_within_range():
    benchmark = {"lower_quartile": 2.0, "upper_quartile": 5.0}
    assert classify_against_benchmark(3.5, benchmark) == "Within Range"


def test_classify_out_of_range():
    benchmark = {"lower_quartile": 2.0, "upper_quartile": 5.0}
    assert classify_against_benchmark(1.0, benchmark) == "Out of Range"


def test_classify_no_benchmark():
    assert classify_against_benchmark(3.5, None) == "No benchmark available"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASSED:", t.__name__)
    print(f"\n{len(tests)} tests passed.")