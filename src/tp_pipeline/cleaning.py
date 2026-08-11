"""
cleaning.py
---------------
Turns raw journal rows into clean, enriched rows: normalizes the company
code, flags intercompany vs. third-party transactions, and derives each
row's transaction group from the GL account mapping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tp_pipeline.exceptions import MappingNotFoundError


def clean_company_code(raw_code):
    return str(raw_code).strip().upper()


def clean_transaction_row(row: dict, gl_mapping: dict):
    company_code = clean_company_code(row["CompanyCode"])
    partner_code = clean_company_code(row.get("PartnerCompanyCode", ""))
    if partner_code in ("NAN", "NONE"):
        partner_code = ""
    is_intercompany = partner_code != ""
    intercompany_label = "IC" if is_intercompany else "3P"
    gl_account = str(row["GLAccount"])
    transaction_group = gl_mapping.get(gl_account, "Unmapped")
    return {
        **row,
        "CompanyCode": company_code,
        "PartnerCompanyCode": partner_code,
        "IsIntercompany": is_intercompany,
        "IntercompanyLabel": intercompany_label,
        "TransactionGroup": transaction_group
    }


def get_transaction_group(gl_account, gl_mapping):
    try:
        return gl_mapping[gl_account]
    except KeyError:
        raise MappingNotFoundError(f"GL account '{gl_account}' has no entry in mapping_gl_accounts.xlsx")


if __name__ == "__main__":
    from tp_pipeline.data_io import read_entity_master, read_mapping_gl_accounts, read_erp_export
    from tp_pipeline.lookups import build_gl_account_mapping_lookup

    gl_mapping = build_gl_account_mapping_lookup(read_mapping_gl_accounts())
    erp_df = read_erp_export()
    show_row = erp_df.iloc[10].to_dict()   # a single row as a dictionary
    print(clean_transaction_row(show_row, gl_mapping))

    gl_mapping = {"4000": "Distribution"}
    print(get_transaction_group("4000", gl_mapping))
    try:
        get_transaction_group("4900", gl_mapping)
    except MappingNotFoundError as e:
        print("Caught error:", e)