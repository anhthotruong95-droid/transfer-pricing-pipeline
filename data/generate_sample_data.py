"""
generate_sample_data.py
------------------------
Creates all 6 Excel files the pharma Transfer Pricing pipeline consumes:

  1. raw_erp_export.xlsx          - SAP-style journal, transaction level
  2. entity_financials.xlsx       - a REAL, simple P&L per legal entity
                                     (Revenue/COGS/SGA/RD/OtherOpex - one
                                     revenue line, no group split - that
                                     split is derived from the journal)
  3. mapping_gl_accounts.xlsx     - GL account -> Transaction Group
  4. benchmark_studies.xlsx       - Region-aware benchmark studies with
                                     Min/LowerQuartile/Median/UpperQuartile/
                                     Max/NumberOfComparables
  5. entity_master.xlsx           - legal entity master data incl. Region
  6. fx_rates.xlsx                - currency -> EUR conversion rate

Design rule that keeps the whole pipeline reconcilable:
  CompanyCode = the entity that RAISES the invoice / recognizes the amount
  as revenue in the journal. PartnerCompanyCode = the intercompany
  counterparty, blank if the counterparty is a third party.

Group structure (pharma "Principal structure", 6 entities, 3 regions):
  US02  = Principal              (Americas) - owns IP, not benchmarked (residual profit)
  US05  = Distributor             (Americas) - NEW: separate from the Principal
  DE01  = Distributor             (EMEA)
  FR03  = Distributor             (EMEA)
  SG01  = Distributor             (APAC)
  CH04  = Contract Manufacturer   (EMEA) - benchmarked on Full Cost Mark-up, not Operating Margin

Amounts are TARGET-DRIVEN: for each entity we decide the metric we want it
to land at, then derive the journal amounts backward from that target.
This run deliberately places:
  - US05's operating margin BELOW the Americas benchmark Min (a genuine
    outlier - narrative: newly launched distributor still ramping up)
  - FR03's royalty rate just ABOVE the global Upper Quartile but inside
    Max (a "grey zone" worth reviewing, not yet a hard outlier)
  - everyone else comfortably inside their interquartile range
"""

import random
from datetime import date, timedelta

import pandas as pd

random.seed(23)

OUT_DIR = "data"

PRINCIPAL = "US02"
MANUFACTURER = "CH04"
DISTRIBUTORS = ["US05", "DE01", "FR03", "SG01"]

CURRENCY_BY_ENTITY = {"US02": "USD", "US05": "USD", "CH04": "CHF", "DE01": "EUR", "FR03": "EUR", "SG01": "SGD"}
REGION_BY_ENTITY = {"US02": "Americas", "US05": "Americas", "CH04": "EMEA",
                    "DE01": "EMEA", "FR03": "EMEA", "SG01": "APAC"}

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
    """Break `total` into n randomly-sized invoice amounts that sum exactly to `total`."""
    weights = [random.uniform(1 - jitter, 1 + jitter) for _ in range(n)]
    weight_sum = sum(weights)
    amounts = [round(total * w / weight_sum, 2) for w in weights]
    amounts[-1] = round(amounts[-1] + (total - sum(amounts)), 2)
    return amounts


# ------------------------------------------------------------------
# 1) TARGET metrics per entity (deliberately including 1 outlier + 1 grey-zone case)
# ------------------------------------------------------------------
distributor_targets = {
    "US05": {"revenue": random.uniform(400_000, 460_000), "margin_pct": -0.8,       # OUTLIER: below Americas Min (0.3)
             "sga_frac": random.uniform(0.09, 0.11), "otheropex_frac": random.uniform(0.025, 0.035),
             "royalty_rate_pct": random.uniform(1.8, 2.2)},
    "DE01": {"revenue": random.uniform(410_000, 470_000), "margin_pct": random.uniform(3.2, 3.9),
             "sga_frac": random.uniform(0.08, 0.10), "otheropex_frac": random.uniform(0.02, 0.03),
             "royalty_rate_pct": random.uniform(1.8, 2.2)},
    "FR03": {"revenue": random.uniform(430_000, 490_000), "margin_pct": random.uniform(2.5, 3.2),
             "sga_frac": random.uniform(0.08, 0.10), "otheropex_frac": random.uniform(0.02, 0.03),
             "royalty_rate_pct": 3.6},                                              # GREY ZONE: above global UQ (3.0), below Max (4.5)
    "SG01": {"revenue": random.uniform(360_000, 420_000), "margin_pct": random.uniform(3.2, 4.2),
             "sga_frac": random.uniform(0.08, 0.10), "otheropex_frac": random.uniform(0.02, 0.03),
             "royalty_rate_pct": random.uniform(2.0, 2.4)},
}

manufacturer_target = {
    "revenue": random.uniform(650_000, 800_000),
    "markup_pct": random.uniform(6.0, 7.2),      # Full Cost Mark-up, inside EMEA CM benchmark 5.0-8.0
    "sga_frac": random.uniform(0.03, 0.045), "rd_frac": random.uniform(0.01, 0.02),
    "otheropex_frac": random.uniform(0.02, 0.03),
    "royalty_rate_pct": random.uniform(1.6, 2.2),
}

# ------------------------------------------------------------------
# 2) Distribution: Principal -> Distributor (IC) + Distributor -> 3P
# ------------------------------------------------------------------
distributor_cogs = {}
distributor_actual_revenue = {}

for d in DISTRIBUTORS:
    t = distributor_targets[d]
    cogs_target = t["revenue"] * (1 - t["margin_pct"] / 100 - t["sga_frac"] - t["otheropex_frac"])
    distributor_cogs[d] = cogs_target

    for amount in split_into_invoices(cogs_target, random.randint(8, 11)):
        add_row(PRINCIPAL, d, "4000", "Invoice", amount,
                f"Verkauf Fertigarzneimittel an Vertriebsgesellschaft {d}")

    n_3p = random.randint(10, 14)
    invoice_total = t["revenue"] * 1.01
    for amount in split_into_invoices(invoice_total, n_3p):
        customer = random.choice(WHOLESALERS_BY_DISTRIBUTOR[d])
        add_row(d, "", "4000", "Invoice", amount, f"Verkauf Fertigware an Grosshaendler {customer}")
    credit_note = -round(t["revenue"] * 0.01, 2)
    add_row(d, "", "4000", "Credit Note", credit_note, "Gutschrift Retoure Grosshandel")

    distributor_actual_revenue[d] = t["revenue"] * 1.01 + credit_note

# ------------------------------------------------------------------
# 3) Contract Manufacturing: Manufacturer -> Principal fee
# ------------------------------------------------------------------
for amount in split_into_invoices(manufacturer_target["revenue"], 6):
    add_row(MANUFACTURER, PRINCIPAL, "4100", "Invoice", amount, "Lohnfertigungsgebuehr API-Produktion")

# ------------------------------------------------------------------
# 4) IP / Licensing: Principal charges royalties (based on each licensee's own net sales)
# ------------------------------------------------------------------
for d in DISTRIBUTORS:
    t = distributor_targets[d]
    royalty_annual = distributor_actual_revenue[d] * t["royalty_rate_pct"] / 100
    for quarter, amount in zip(["Q1", "Q2", "Q3", "Q4"], split_into_invoices(royalty_annual, 4, jitter=0.1)):
        add_row(PRINCIPAL, d, "4200", "Invoice", amount, f"Lizenzgebuehr Marke/Patent {quarter} 2025 - {d}")

royalty_annual_manufacturer = manufacturer_target["revenue"] * manufacturer_target["royalty_rate_pct"] / 100
for quarter, amount in zip(["Q1", "Q2", "Q3", "Q4"], split_into_invoices(royalty_annual_manufacturer, 4, jitter=0.1)):
    add_row(PRINCIPAL, MANUFACTURER, "4200", "Invoice", amount,
            f"Lizenzgebuehr Herstellungs-Know-how {quarter} 2025 - {MANUFACTURER}")

# ------------------------------------------------------------------
# 5) Noise: unmapped GL account (4900) - intentional, for the error-handling chapter
# ------------------------------------------------------------------
all_entities = [PRINCIPAL, MANUFACTURER] + DISTRIBUTORS
for _ in range(16):
    company = random.choice(all_entities)
    partner = random.choice([e for e in all_entities if e != company] + [""])
    amount = round(random.uniform(200, 5_000), 2)
    add_row(company, partner, "4900", random.choice(["Invoice", "Credit Note"]), amount,
            "Sonstige Kosten - noch nicht klassifiziert")

erp_df = pd.DataFrame(rows).sort_values("TransactionID").reset_index(drop=True)
erp_df.to_excel(f"{OUT_DIR}/raw_erp_export.xlsx", sheet_name="Journal", index=False)


# ------------------------------------------------------------------
# entity_financials.xlsx - a REAL simple P&L: one Revenue line, derived
# from the SAME journal actuals so reconciliation ties out exactly.
# ------------------------------------------------------------------
def journal_revenue_sum(company, gl_accounts):
    mask = (erp_df.CompanyCode == company) & (erp_df.GLAccount.astype(str).isin(gl_accounts))
    return round(erp_df.loc[mask, "Amount"].sum(), 2)


financials_rows = []
for d in DISTRIBUTORS:
    t = distributor_targets[d]
    revenue_actual = journal_revenue_sum(d, ["4000"])
    financials_rows.append({
        "CompanyCode": d, "Period": "FY2025", "Revenue": revenue_actual,
        "COGS": round(distributor_cogs[d], 2),
        "SGA": round(revenue_actual * t["sga_frac"], 2),
        "RD": 0.0,
        "OtherOpex": round(revenue_actual * t["otheropex_frac"], 2),
    })

cm_revenue_actual = journal_revenue_sum(MANUFACTURER, ["4100"])
# Full Cost Mark-up = OperatingProfit / TotalCost  =>  OperatingProfit = markup * Revenue / (1 + markup)
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

principal_ic_revenue = journal_revenue_sum(PRINCIPAL, ["4000"])
principal_licensing_revenue = journal_revenue_sum(PRINCIPAL, ["4200"])
principal_revenue_total = round(principal_ic_revenue + principal_licensing_revenue, 2)
raw_material_cost = cm_revenue_actual * random.uniform(0.08, 0.15)
principal_cogs = cm_revenue_actual + raw_material_cost
principal_sga_frac = random.uniform(0.06, 0.08)
principal_otheropex_frac = random.uniform(0.02, 0.03)
principal_target_margin_frac = random.uniform(0.12, 0.18)
principal_sga = principal_revenue_total * principal_sga_frac
principal_otheropex = principal_revenue_total * principal_otheropex_frac
principal_target_margin_amount = principal_revenue_total * principal_target_margin_frac
principal_rd = principal_revenue_total - principal_cogs - principal_sga - principal_otheropex - principal_target_margin_amount
financials_rows.append({
    "CompanyCode": PRINCIPAL, "Period": "FY2025", "Revenue": principal_revenue_total,
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
    {"GLAccount": "4200", "TransactionGroup": "IP / Licensing"},
]).to_excel(f"{OUT_DIR}/mapping_gl_accounts.xlsx", sheet_name="Mapping", index=False)

# ------------------------------------------------------------------
# benchmark_studies.xlsx - region-aware, with full quartile statistics
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
    {"TransactionGroup": "IP / Licensing", "Region": "Global", "BenchmarkMetric": "Royalty Rate (% of Net Sales)",
     "Min": 0.2, "LowerQuartile": 1.0, "Median": 1.8, "UpperQuartile": 3.0, "Max": 4.5,
     "NumberOfComparables": 9, "StudySource": "Comparable Uncontrolled Royalty Database 2024", "Year": 2024},
]).to_excel(f"{OUT_DIR}/benchmark_studies.xlsx", sheet_name="Benchmarks", index=False)

# ------------------------------------------------------------------
# entity_master.xlsx - now includes Region
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
# fx_rates.xlsx - group reporting currency = EUR
# ------------------------------------------------------------------
pd.DataFrame([
    {"Currency": "EUR", "RateToEUR": 1.00, "Period": "FY2025"},
    {"Currency": "USD", "RateToEUR": 0.92, "Period": "FY2025"},
    {"Currency": "CHF", "RateToEUR": 1.04, "Period": "FY2025"},
    {"Currency": "SGD", "RateToEUR": 0.68, "Period": "FY2025"},
]).to_excel(f"{OUT_DIR}/fx_rates.xlsx", sheet_name="FxRates", index=False)

print("Sample data created:")
print(" - raw_erp_export.xlsx      ", erp_df.shape)
print(" - entity_financials.xlsx   ", financials_df.shape)
print(" - benchmark_studies.xlsx   ", "6 rows (region-aware + quartiles)")
print(" - entity_master.xlsx       ", "6 entities (incl. Region)")
print(" - fx_rates.xlsx            ", "4 currencies")
print("\nJournal total amount:", round(erp_df["Amount"].sum(), 2))
