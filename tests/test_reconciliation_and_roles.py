"""
test_reconciliation.py
---------------------------
Unit tests for tp_pipeline.reconciliation: the intercompany/third-party
flag and the total-reconciliation tolerance check.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
from tp_pipeline.reconciliation import flag_intercompany, reconciles


def test_flag_intercompany_true_when_partner_filled():
    df = pd.DataFrame({"PartnerCompanyCode": ["DE01", "", None]})
    result = flag_intercompany(df).tolist()
    assert result == [True, False, False], f"Expected [True, False, False], got {result!r}"


def test_reconciles_within_tolerance():
    result = reconciles(1000.0, 1000.5, tolerance=1.0)
    assert result is True, f"Expected True, got {result!r}"


def test_reconciles_outside_tolerance():
    result = reconciles(1000.0, 1050.0, tolerance=1.0)
    assert result is False, f"Expected False, got {result!r}"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASSED:", t.__name__)
    print(f"\n{len(tests)} tests passed.")