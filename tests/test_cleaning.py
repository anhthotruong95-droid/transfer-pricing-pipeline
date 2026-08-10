"""
test_cleaning.py
--------------------
Unit tests for tp_pipeline.cleaning: company code normalization, row
cleaning, and the error handling around unmapped GL accounts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tp_pipeline.cleaning import clean_company_code, clean_transaction_row, get_transaction_group
from tp_pipeline.exceptions import MappingNotFoundError

GL_MAPPING = {"4000": "Distribution", "4100": "Contract Manufacturing"}


def test_clean_company_code_strips_and_uppercases():
    result = clean_company_code(" de01 ")
    assert result == "DE01", f"Expected 'DE01', got {result!r}"


def test_clean_company_code_handles_nan():
    import math
    result = clean_company_code(math.nan)
    assert result == "NAN", f"Expected 'NAN', got {result!r}"


def test_clean_transaction_row_flags_intercompany():
    row = {"CompanyCode": " us02 ", "PartnerCompanyCode": "de01", "GLAccount": "4000"}
    cleaned = clean_transaction_row(row, GL_MAPPING)
    assert cleaned["CompanyCode"] == "US02", f"Expected 'US02', got {cleaned['CompanyCode']!r}"
    assert cleaned["IsIntercompany"] is True, f"Expected True, got {cleaned['IsIntercompany']!r}"
    assert cleaned["TransactionGroup"] == "Distribution", f"Expected 'Distribution', got {cleaned['TransactionGroup']!r}"


def test_clean_transaction_row_flags_third_party():
    row = {"CompanyCode": "DE01", "PartnerCompanyCode": "", "GLAccount": "4000"}
    cleaned = clean_transaction_row(row, GL_MAPPING)
    assert cleaned["IsIntercompany"] is False, f"Expected False, got {cleaned['IsIntercompany']!r}"


def test_get_transaction_group_known_account():
    result = get_transaction_group("4000", GL_MAPPING)
    assert result == "Distribution", f"Expected 'Distribution', got {result!r}"


def test_get_transaction_group_unknown_account_raises():
    try:
        get_transaction_group("4900", GL_MAPPING)
        assert False, "Expected MappingNotFoundError to be raised for GL account '4900', but nothing was raised"
    except MappingNotFoundError:
        pass


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASSED:", t.__name__)
    print(f"\n{len(tests)} tests passed.")