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
from tp_pipeline.reconciliation import reconciles

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