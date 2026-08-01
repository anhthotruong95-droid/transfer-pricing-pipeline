"""
roles.py
------------
Derives every functional role an entity plays (Distributor, Contract
Manufacturer, Principal / IP Owner) from the distinct transaction groups
it invoices in the journal - an entity can hold more than one role.
"""


def derive_functional_roles(company_code, transactions, gl_mapping):
    gl_accounts_used = {
        t["GLAccount"] for t in transactions
        if t["CompanyCode"] == company_code and t["GLAccount"] != "4900"
    }

    if not gl_accounts_used:
        return ["Unknown"]

    groups_used = {gl_mapping.get(gl, "Unknown") for gl in gl_accounts_used}

    roles = []
    for group in groups_used:
        if group == "Contract Manufacturing":
            roles.append("Contract Manufacturer")
        elif group == "IP / Licensing":
            roles.append("Principal / IP Owner")
        elif group == "Distribution":
            dist_rows = [t for t in transactions if t["CompanyCode"] == company_code and t["GLAccount"] in gl_accounts_used and gl_mapping.get(t["GLAccount"]) == "Distribution"]
            ic_count = sum(1 for t in dist_rows if t["PartnerCompanyCode"])
            if ic_count > len(dist_rows) / 2:
                roles.append("Principal")
            else:
                roles.append("Distributor")
        else:
            roles.append("Unknown")

    return roles


if __name__ == "__main__":
    gl_mapping = {"4000": "Distribution", "4100": "Contract Manufacturing", "4200": "IP / Licensing"}

    sample_transactions = [
        {"CompanyCode": "US02", "PartnerCompanyCode": "DE01", "GLAccount": "4000"},
        {"CompanyCode": "US02", "PartnerCompanyCode": "FR03", "GLAccount": "4000"},
        {"CompanyCode": "CH04", "PartnerCompanyCode": "US02", "GLAccount": "4100"},
        {"CompanyCode": "CH04", "PartnerCompanyCode": "", "GLAccount": "4000"},   # <- CH04 vertreibt jetzt zusätzlich
    ]

    print(derive_functional_roles("US02", sample_transactions, gl_mapping))
    print(derive_functional_roles("CH04", sample_transactions, gl_mapping))