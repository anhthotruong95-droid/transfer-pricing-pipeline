"""
reconciliation.py
---------------------
Flags journal rows as intercompany vs. third party, and checks whether
two totals (e.g. journal vs. financials) tie out within a small tolerance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def flag_intercompany(df):
    return df["PartnerCompanyCode"].notna() & (df["PartnerCompanyCode"].astype(str).str.strip() != "")


def reconciles(original_total, comparison_total, tolerance=1.0):
    return abs(original_total - comparison_total) <= tolerance


if __name__ == "__main__":
    from tp_pipeline.data_io import read_erp_export

    df = read_erp_export()
    df["IsIntercompany"] = flag_intercompany(df)
    print(df[["CompanyCode", "PartnerCompanyCode", "IsIntercompany"]].head(6))

    original_total = df["Amount"].sum()
    recombined_total = df.loc[df["IsIntercompany"], "Amount"].sum() + df.loc[~df["IsIntercompany"], "Amount"].sum()
    print("Original:", original_total, "| Neu zusammengesetzt:", recombined_total)
    print("Reconciles?", reconciles(original_total, recombined_total))