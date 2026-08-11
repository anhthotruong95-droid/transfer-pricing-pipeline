"""
test_integration.py
------------------------
Integration tests that check the pipeline's output files reconcile
against each other and against the raw source journal. Unlike the other
test files, these read real files from data/ and output/ instead of
using hand-built sample data - so run `python3 data/generate_sample_data.py`
and `python3 main.py` first to make sure both are up to date.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

TOLERANCE = 1.0


def test_unmapped_total_matches_journal_gl4900_total():
    """The amounts in unmapped_transactions.csv should sum to exactly the
    same total as the raw journal's GL-4900 rows - nothing should be lost
    or added while routing unmapped rows to the data-quality log."""
    journal = pd.read_excel(DATA_DIR / "raw_erp_export.xlsx", sheet_name="Journal")
    journal_gl4900_total = journal.loc[journal["GLAccount"].astype(str) == "4900", "Amount"].sum()

    unmapped = pd.read_csv(OUTPUT_DIR / "unmapped_transactions.csv")
    unmapped_total = unmapped["Amount"].sum()

    diff = abs(journal_gl4900_total - unmapped_total)
    print(f"    Journal GL-4900 total:   {journal_gl4900_total:>15,.2f}")
    print(f"    unmapped_transactions:   {unmapped_total:>15,.2f}")
    print(f"    Difference:              {diff:>15,.2f}")

    assert diff <= TOLERANCE, (
        f"Unmapped total ({unmapped_total:,.2f}) does not match journal "
        f"GL-4900 total ({journal_gl4900_total:,.2f}), difference: {diff:,.2f}"
    )


def test_ic_volume_matches_journal_ic_total_in_eur():
    """The EUR total across intercompany_transaction_volume.csv should
    match the EUR-converted total of every intercompany, mapped row in
    the raw journal - the summary should neither drop nor double-count
    any intercompany transaction."""
    journal = pd.read_excel(DATA_DIR / "raw_erp_export.xlsx", sheet_name="Journal")
    fx_df = pd.read_excel(DATA_DIR / "fx_rates.xlsx", sheet_name="FxRates")
    fx_rate_lookup = dict(zip(fx_df["Currency"], fx_df["RateToEUR"]))

    journal["PartnerCompanyCode"] = journal["PartnerCompanyCode"].fillna("").astype(str)
    is_intercompany = journal["PartnerCompanyCode"].str.strip() != ""
    is_mapped = journal["GLAccount"].astype(str) != "4900"
    ic_journal = journal.loc[is_intercompany & is_mapped]

    journal_ic_total_eur = sum(
        row["Amount"] * fx_rate_lookup[row["Currency"]]
        for _, row in ic_journal.iterrows()
    )

    ic_volume = pd.read_csv(OUTPUT_DIR / "intercompany_transaction_volume.csv")
    ic_volume_total_eur = ic_volume["TotalAmountEUR"].sum()

    diff = abs(journal_ic_total_eur - ic_volume_total_eur)
    print(f"    Journal IC total (EUR):  {journal_ic_total_eur:>15,.2f}")
    print(f"    IC volume total (EUR):   {ic_volume_total_eur:>15,.2f}")
    print(f"    Difference:              {diff:>15,.2f}")

    assert diff <= TOLERANCE, (
        f"IC volume total ({ic_volume_total_eur:,.2f} EUR) does not match "
        f"journal IC total ({journal_ic_total_eur:,.2f} EUR), "
        f"difference: {diff:,.2f}"
    )


def test_financial_statements_revenue_matches_mapped_journal_total():
    """The RevenueLC total across financial_statements.csv should match
    the raw journal total minus the unmapped GL-4900 amounts - this is
    the same tie-out the pipeline itself checks in Step 5, verified here
    directly from the exported files."""
    journal = pd.read_excel(DATA_DIR / "raw_erp_export.xlsx", sheet_name="Journal")
    journal_total = journal["Amount"].sum()

    unmapped = pd.read_csv(OUTPUT_DIR / "unmapped_transactions.csv")
    unmapped_total = unmapped["Amount"].sum()

    mapped_journal_total = journal_total - unmapped_total

    financials = pd.read_csv(OUTPUT_DIR / "financial_statements.csv")
    revenue_total = financials["RevenueLC"].sum()

    diff = abs(mapped_journal_total - revenue_total)
    print(f"    Journal total (raw):     {journal_total:>15,.2f}")
    print(f"    Unmapped total:          {unmapped_total:>15,.2f}")
    print(f"    Mapped journal total:    {mapped_journal_total:>15,.2f}")
    print(f"    financial_statements:    {revenue_total:>15,.2f}")
    print(f"    Difference:              {diff:>15,.2f}")

    assert diff <= TOLERANCE, (
        f"financial_statements.csv RevenueLC total ({revenue_total:,.2f}) "
        f"does not match mapped journal total ({mapped_journal_total:,.2f}), "
        f"difference: {diff:,.2f}"
    )


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        description = (t.__doc__ or "").strip().split("\n")[0]
        print(f"\n--- {t.__name__} ---")
        print(f"    {description}")
        t()
        print(f"PASSED: {t.__name__}")
    print(f"\n{len(tests)} tests passed.")
