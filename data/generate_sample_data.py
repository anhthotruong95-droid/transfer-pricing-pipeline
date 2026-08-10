"""
generate_sample_data.py
------------------------
Creates the 5 Excel files for the pharma Transfer Pricing pipeline
(Distribution and Contract Manufacturing only).

Every entity's own P&L (entity_financials.xlsx) is denominated in ITS OWN
local currency. Whenever an invoice crosses between two entities with
different currencies, the journal amount is FX-converted into the
INVOICING party's currency, so that both files tie out consistently once
converted to a common reporting currency (EUR).
"""

import random
from datetime import date, timedelta

import pandas as pd

random.seed(11)

OUT_DIR = "data"

PRINCIPAL = "US02"
MANUFACTURER = "CH04"
DISTRIBUTORS = ["US05", "DE01", "FR03", "SG01"]

CURRENCY_BY_ENTITY = {"US02": "USD", "US05": "USD", "CH04": "CHF", "DE01": "EUR", "FR03": "EUR", "SG01": "SGD"}
REGION_BY_ENTITY = {"US02": "Americas", "US05": "Americas", "CH04": "EMEA",
                    "DE01": "EMEA", "FR03": "EMEA", "SG01": "APAC"}
FX_TO_EUR = {"EUR": 1.00, "USD": 0.92, "CHF": 1.04, "SGD": 0.68}


def convert(amount, from_currency, to_currency):
    """Converts an amount between two currencies via their EUR rates."""
    return amount * FX_TO_EUR[from_currency] / FX_TO_EUR[to_currency]


WHOLESALERS_BY_DISTRIBUTOR = {
    "US05": ["McKesson Specialty Distribution", "AmerisourceBergen Pharma", "Cardinal Health East"],
    "DE01": ["Phoenix Pharmahandel AG", "Apothekengenossenschaft Nord", "MedGross Deutschland"],
    "FR03": ["CERP Rouen Distribution", "OCP Pharma France", "Pharmacie Centrale Lyon"],
    "SG01": ["Zuellig Pharma Singapore", "DKSH Healthcare Asia", "Singapore MedSupply"],
}

start = date(2025, 1, 1)
rows = []
tx_id = 1


def random_date():
    return (start + timedelta(days=random.randint(0, 364))).isoformat()


def add_row(company, partner, gl_account, tx_type, amount, booking_text):
    global tx_id
    rows.append({
        "TransactionID": f"TX{tx_id:05d}", "PostingDate": random_date(), "BookingText": booking_text,
        "CompanyCode": company, "PartnerCompanyCode": partner, "GLAccount": gl_account,
        "TransactionType": tx_type, "Amount": round(amount, 2), "Currency": CURRENCY_BY_ENTITY[company],
    })
    tx_id += 1


def split_into_invoices(total, n, jitter=0.3):
    weights = [random.uniform(1 - jitter, 1 + jitter) for _ in range(n)]
    weight_sum = sum(weights)
    amounts = [round(total * w / weight_sum, 2) for w in weights]
    amounts[-1] = round(amounts[-1] + (total - sum(amounts)), 2)
    return amounts


# ------------------------------------------------------------------
# 1) TARGET metrics per entity - all figures are in the ENTITY'S OWN currency
# ------------------------------------------------------------------
distributor_targets = {
    "US05": {"revenue": random.uniform(400_000, 460_000), "margin_pct": random.uniform(0.5, 1.5), 
             "sga_frac": random.uniform(0.09, 0.11), "otheropex_frac": random.uniform(0.025, 0.035)},
    "DE01": {"revenue": random.uniform(410_000, 470_000), "margin_pct": random.uniform(3.2, 3.9),
             "sga_frac": random.uniform(0.08, 0.10), "otheropex_frac": random.uniform(0.02, 0.03)},
    "FR03": {"revenue": random.uniform(430_000, 490_000), "margin_pct": random.uniform(2.5, 3.2),
             "sga_frac": random.uniform(0.08, 0.10), "otheropex_frac": random.uniform(0.02, 0.03)},
    "SG01": {"revenue": random.uniform(360_000, 420_000), "margin_pct": random.uniform(3.2, 4.2),
             "sga_frac": random.uniform(0.08, 0.10), "otheropex_frac": random.uniform(0.02, 0.03)},
}

manufacturer_target = {
    "revenue": random.uniform(650_000, 800_000),
    "markup_pct": random.uniform(6.0, 7.2),
    "sga_frac": random.uniform(0.03, 0.045), "rd_frac": random.uniform(0.01, 0.02),
    "otheropex_frac": random.uniform(0.02, 0.03),
}

# ------------------------------------------------------------------
# 2) Distribution: Principal -> Distributor (IC) + Distributor -> 3P
#    distributor_cogs[d] is the distributor's COGS in ITS OWN currency.
#    The journal invoice from the Principal must be FX-converted into the
#    Principal's own currency (USD) - it is not the same raw number.
# ------------------------------------------------------------------
distributor_cogs = {}

for d in DISTRIBUTORS:
    t = distributor_targets[d]
    cogs_target_local = t["revenue"] * (1 - t["margin_pct"] / 100 - t["sga_frac"] - t["otheropex_frac"])
    distributor_cogs[d] = cogs_target_local  # stays in distributor's own currency, used for entity_financials

    cogs_target_usd = convert(cogs_target_local, CURRENCY_BY_ENTITY[d], CURRENCY_BY_ENTITY[PRINCIPAL])
    for amount in split_into_invoices(cogs_target_usd, random.randint(16, 22)):
        add_row(PRINCIPAL, d, "4000", "Invoice", amount,
                f"Sale of finished pharmaceuticals to distributor {d}")

    n_3p = random.randint(20, 28)
    invoice_total = t["revenue"] * 1.01
    for amount in split_into_invoices(invoice_total, n_3p):
        customer = random.choice(WHOLESALERS_BY_DISTRIBUTOR[d])
        add_row(d, "", "4000", "Invoice", amount, f"Sale of finished goods to wholesaler {customer}")
    credit_note = -round(t["revenue"] * 0.01, 2)
    add_row(d, "", "4000", "Credit Note", credit_note, "Credit note wholesale return")

# ------------------------------------------------------------------
# 3) Contract Manufacturing: Manufacturer -> Principal fee
#    CH04 books its own fee revenue in CHF (its own currency) - self
#    consistent, no conversion needed on this side.
# ------------------------------------------------------------------
for amount in split_into_invoices(manufacturer_target["revenue"], 12):
    add_row(MANUFACTURER, PRINCIPAL, "4100", "Invoice", amount, "Contract manufacturing fee API production")

# ------------------------------------------------------------------
# 4) Noise: unmapped GL account (4900) - intentional, for the error-handling chapter
# ------------------------------------------------------------------
all_entities = [PRINCIPAL, MANUFACTURER] + DISTRIBUTORS
for _ in range(32):
    company = random.choice(all_entities)
    partner = random.choice([e for e in all_entities if e != company] + [""])
    amount = round(random.uniform(200, 5_000), 2)
    add_row(company, partner, "4900", random.choice(["Invoice", "Credit Note"]), amount,
            "Other costs - not classified")

erp_df = pd.DataFrame(rows).sort_values("TransactionID").reset_index(drop=True)
erp_df.to_excel(f"{OUT_DIR}/raw_erp_export.xlsx", sheet_name="Journal", index=False)


# ------------------------------------------------------------------
# entity_financials.xlsx - each entity's P&L in ITS OWN currency
# ------------------------------------------------------------------
def journal_revenue_sum(company, gl_accounts):
    mask = (erp_df.CompanyCode == company) & (erp_df.GLAccount.astype(str).isin(gl_accounts))
    return round(erp_df.loc[mask, "Amount"].sum(), 2)


financials_rows = []
for d in DISTRIBUTORS:
    t = distributor_targets[d]
    revenue_actual = journal_revenue_sum(d, ["4000"])  # distributor's own 3P sales, already in its own currency
    financials_rows.append({
        "CompanyCode": d, "Period": "FY2025", "Revenue": revenue_actual,
        "COGS": round(distributor_cogs[d], 2),  # in distributor's own currency, matches the FX-converted journal invoice
        "SGA": round(revenue_actual * t["sga_frac"], 2),
        "RD": 0.0,
        "OtherOpex": round(revenue_actual * t["otheropex_frac"], 2),
    })

cm_revenue_actual = journal_revenue_sum(MANUFACTURER, ["4100"])  # CH04's own fee revenue, in CHF
markup_frac = manufacturer_target["markup_pct"] / 100
cm_operating_profit = markup_frac * cm_revenue_actual / (1 + markup_frac)
cm_total_cost = cm_revenue_actual - cm_operating_profit
financials_rows.append({
    "CompanyCode": MANUFACTURER, "Period": "FY2025", "Revenue": cm_revenue_actual,
    "COGS": round(cm_total_cost * (1 - manufacturer_target["sga_frac"] - manufacturer_target["rd_frac"]
                                    - manufacturer_target["otheropex_frac"]), 2),
    "SGA": round(cm_total_cost * manufacturer_target["sga_frac"], 2),
    "RD": round(cm_total_cost * manufacturer_target["rd_frac"], 2),
    "OtherOpex": round(cm_total_cost * manufacturer_target["otheropex_frac"], 2),
})

principal_revenue = journal_revenue_sum(PRINCIPAL, ["4000"])  # Principal's own IC sales, already in USD

# The CM fee CH04 charges is in CHF - must be converted to USD before it
# becomes part of the Principal's (USD) COGS.
cm_fee_in_usd = convert(cm_revenue_actual, CURRENCY_BY_ENTITY[MANUFACTURER], CURRENCY_BY_ENTITY[PRINCIPAL])
raw_material_cost = cm_fee_in_usd * random.uniform(0.08, 0.15)
principal_cogs = cm_fee_in_usd + raw_material_cost

principal_sga_frac = random.uniform(0.06, 0.08)
principal_otheropex_frac = random.uniform(0.02, 0.03)
principal_target_margin_frac = random.uniform(0.12, 0.18)
principal_sga = principal_revenue * principal_sga_frac
principal_otheropex = principal_revenue * principal_otheropex_frac
principal_target_margin_amount = principal_revenue * principal_target_margin_frac
principal_rd = principal_revenue - principal_cogs - principal_sga - principal_otheropex - principal_target_margin_amount
financials_rows.append({
    "CompanyCode": PRINCIPAL, "Period": "FY2025", "Revenue": principal_revenue,
    "COGS": round(principal_cogs, 2), "SGA": round(principal_sga, 2),
    "RD": round(principal_rd, 2), "OtherOpex": round(principal_otheropex, 2),
})

financials_df = pd.DataFrame(financials_rows)
financials_df.to_excel(f"{OUT_DIR}/entity_financials.xlsx", sheet_name="Financials", index=False)

# ------------------------------------------------------------------
# mapping_gl_accounts.xlsx
# ------------------------------------------------------------------
pd.DataFrame([
    {"GLAccount": "4000", "TransactionGroup": "Distribution"},
    {"GLAccount": "4100", "TransactionGroup": "Contract Manufacturing"},
]).to_excel(f"{OUT_DIR}/mapping_gl_accounts.xlsx", sheet_name="Mapping", index=False)

# ------------------------------------------------------------------
# benchmark_studies.xlsx
# ------------------------------------------------------------------
pd.DataFrame([
    {"TransactionGroup": "Distribution", "Region": "EMEA", "BenchmarkMetric": "Operating Margin (%)",
     "Min": 0.5, "LowerQuartile": 2.0, "Median": 3.2, "UpperQuartile": 5.0, "Max": 7.8,
     "NumberOfComparables": 18, "StudySource": "Distributor Benchmark Study EMEA Pharma 2024", "Year": 2024},
    {"TransactionGroup": "Distribution", "Region": "APAC", "BenchmarkMetric": "Operating Margin (%)",
     "Min": 0.8, "LowerQuartile": 2.5, "Median": 3.9, "UpperQuartile": 6.0, "Max": 8.5,
     "NumberOfComparables": 14, "StudySource": "Distributor Benchmark Study APAC Pharma 2024", "Year": 2024},
    {"TransactionGroup": "Distribution", "Region": "Americas", "BenchmarkMetric": "Operating Margin (%)",
     "Min": 0.3, "LowerQuartile": 2.0, "Median": 3.0, "UpperQuartile": 4.5, "Max": 6.9,
     "NumberOfComparables": 21, "StudySource": "Distributor Benchmark Study Americas Pharma 2024", "Year": 2024},
    {"TransactionGroup": "Contract Manufacturing", "Region": "EMEA", "BenchmarkMetric": "Full Cost Mark-up (%)",
     "Min": 2.1, "LowerQuartile": 5.0, "Median": 6.4, "UpperQuartile": 8.0, "Max": 10.5,
     "NumberOfComparables": 12, "StudySource": "Contract Manufacturer Benchmark Study EMEA Pharma 2024", "Year": 2024},
]).to_excel(f"{OUT_DIR}/benchmark_studies.xlsx", sheet_name="Benchmarks", index=False)

# ------------------------------------------------------------------
# entity_master.xlsx
# ------------------------------------------------------------------
pd.DataFrame([
    {"CompanyCode": "US02", "LegalEntityName": "PharmaCorp Global Principal Inc.",
     "CountryISO": "US", "CountryName": "United States", "Region": "Americas", "Currency": "USD"},
    {"CompanyCode": "US05", "LegalEntityName": "PharmaCorp USA Distribution Inc.",
     "CountryISO": "US", "CountryName": "United States", "Region": "Americas", "Currency": "USD"},
    {"CompanyCode": "CH04", "LegalEntityName": "PharmaCorp Manufacturing AG",
     "CountryISO": "CH", "CountryName": "Switzerland", "Region": "EMEA", "Currency": "CHF"},
    {"CompanyCode": "DE01", "LegalEntityName": "PharmaCorp Deutschland GmbH",
     "CountryISO": "DE", "CountryName": "Germany", "Region": "EMEA", "Currency": "EUR"},
    {"CompanyCode": "FR03", "LegalEntityName": "PharmaCorp France SAS",
     "CountryISO": "FR", "CountryName": "France", "Region": "EMEA", "Currency": "EUR"},
    {"CompanyCode": "SG01", "LegalEntityName": "PharmaCorp Singapore Pte Ltd",
     "CountryISO": "SG", "CountryName": "Singapore", "Region": "APAC", "Currency": "SGD"},
]).to_excel(f"{OUT_DIR}/entity_master.xlsx", sheet_name="EntityMaster", index=False)

# ------------------------------------------------------------------
# fx_rates.xlsx
# ------------------------------------------------------------------
pd.DataFrame([
    {"Currency": c, "RateToEUR": r, "Period": "FY2025"} for c, r in FX_TO_EUR.items()
]).to_excel(f"{OUT_DIR}/fx_rates.xlsx", sheet_name="FxRates", index=False)

print("Sample data created:")
print(" - raw_erp_export.xlsx      ", erp_df.shape)
print(" - entity_financials.xlsx   ", financials_df.shape)
print("\nJournal total amount (mixed currencies):", round(erp_df["Amount"].sum(), 2))