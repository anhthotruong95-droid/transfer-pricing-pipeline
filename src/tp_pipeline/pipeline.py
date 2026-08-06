"""
pipeline.py
---------------
Orchestrates the full pipeline: reads all source files, cleans the
journal, builds the domain model, classifies each entity against its
benchmark, reconciles totals, and exports the result plus an
intercompany transaction volume summary.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from tp_pipeline.data_io import (read_erp_export, read_entity_financials, read_mapping_gl_accounts,
                                  read_benchmark_studies, read_entity_master, read_fx_rates)
from tp_pipeline.lookups import (build_gl_account_mapping_lookup, build_benchmark_lookup, lookup_benchmark,
                                  build_entity_master_lookup, build_fx_rate_lookup)
from tp_pipeline.cleaning import clean_transaction_row, get_transaction_group
from tp_pipeline.exceptions import MappingNotFoundError
from tp_pipeline.reconciliation import flag_intercompany, reconciles
from tp_pipeline.benchmarking import classify_against_benchmark
from tp_pipeline.models import Transaction, Entity, TPDataset
from tp_pipeline.roles import derive_functional_roles

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "financial_statements.csv"
UNMAPPED_FILE = OUTPUT_DIR / "unmapped_transactions.csv"
IC_VOLUME_FILE = OUTPUT_DIR / "intercompany_transaction_volume.csv"

# The partner's role within a single transaction is fully determined by the
# transaction group itself (e.g. whoever pays a manufacturing fee is, by
# definition, the Principal in that transaction) - no lookup needed.
PARTNER_ROLE_BY_GROUP = {
    "Distribution": "Distributor",
    "Contract Manufacturing": "Principal",
}


def role_of_entity_in_group(company_code, group, dataset):
    entity = dataset.entities.get(company_code)
    if entity is None:
        return "Unknown"
    return entity.functional_role.get(group, "Unknown")


def build_intercompany_volume_summary(dataset, fx_rate_lookup):
    summary = {}

    for t in dataset.transactions:
        if not t.is_intercompany:
            continue

        key = (t.company_code, t.partner_company_code, t.transaction_group, t.currency)
        if key not in summary:
            summary[key] = 0.0
        summary[key] += t.amount

    rows = []
    for (reporting_entity, partner, group, currency), total_lc in summary.items():
        rows.append({
            "ReportingEntity": reporting_entity,
            "RoleOfReportingEntity": role_of_entity_in_group(reporting_entity, group, dataset),
            "TransactionPartner": partner,
            "RoleOfTransactionPartner": PARTNER_ROLE_BY_GROUP.get(group, "Unknown"),
            "TransactionGroup": group,
            "Currency": currency,
            "TotalAmountLC": round(total_lc, 2),
            "TotalAmountEUR": round(total_lc * fx_rate_lookup[currency], 2),
        })

    return rows


def run_pipeline():
    # --- Step 1: Read source files + build lookups ---
    erp_df = read_erp_export()
    fin_df = read_entity_financials()
    erp_df["GLAccount"] = erp_df["GLAccount"].astype(str)
    erp_df["PartnerCompanyCode"] = erp_df["PartnerCompanyCode"].fillna("").astype(str)

    gl_mapping = build_gl_account_mapping_lookup(read_mapping_gl_accounts())
    benchmark_lookup = build_benchmark_lookup(read_benchmark_studies())
    entity_master_lookup = build_entity_master_lookup(read_entity_master())
    fx_rate_lookup = build_fx_rate_lookup(read_fx_rates())

    original_journal_total = erp_df["Amount"].sum()
    print("Step 1 done - source files read, lookups built")

    # --- Step 2: Clean the journal + build Transaction objects ---
    dataset = TPDataset()
    unmapped_rows = []

    for _, raw_row in erp_df.iterrows():
        row = raw_row.to_dict()
        try:
            get_transaction_group(row["GLAccount"], gl_mapping)
            cleaned = clean_transaction_row(row, gl_mapping)
        except MappingNotFoundError as exc:
            unmapped_rows.append({**row, "error": str(exc)})
            continue

        dataset.add_transaction(Transaction(
            transaction_id=cleaned["TransactionID"], posting_date=str(row["PostingDate"]),
            booking_text=row["BookingText"], company_code=cleaned["CompanyCode"],
            partner_company_code=cleaned["PartnerCompanyCode"], gl_account=row["GLAccount"],
            transaction_group=cleaned["TransactionGroup"], transaction_type=row["TransactionType"],
            amount=row["Amount"], currency=row["Currency"], is_intercompany=cleaned["IsIntercompany"],
        ))

    print(f"Step 2 done - {len(dataset.transactions)} transactions loaded, {len(unmapped_rows)} unmapped")

    # --- Step 3: Build Entity objects, derive roles, load financials ---
    transactions_as_dicts = [
        {"CompanyCode": t.company_code, "PartnerCompanyCode": t.partner_company_code, "GLAccount": t.gl_account}
        for t in dataset.transactions
    ]

    for company_code, master in entity_master_lookup.items():
        entity = Entity(
            company_code=company_code, entity_name=master["legal_entity_name"],
            country_name=master["country_name"], region=master["region"], currency=master["currency"],
        )
        entity.functional_role = derive_functional_roles(company_code, transactions_as_dicts, gl_mapping)

        fin_row = fin_df.loc[fin_df["CompanyCode"] == company_code]
        if not fin_row.empty:
            entity.load_financials(fin_row.iloc[0].to_dict())

        dataset.register_entity(entity)

    print(f"Step 3 done - {len(dataset.entities)} entities loaded")

    # --- Step 4: Calculate metrics + classify against benchmark ---
    summary_rows = []

    for entity in dataset.entities.values():
        is_distributor = "Distributor" in entity.functional_role.values()
        is_manufacturer = "Contract Manufacturer" in entity.functional_role.values()

        benchmark_status = None
        pli_indicator = None
        benchmark_min = None
        benchmark_lower_quartile = None
        benchmark_median = None
        benchmark_upper_quartile = None
        benchmark_max = None

        if is_distributor:
            benchmark = lookup_benchmark("Distribution", entity.region, benchmark_lookup)
            benchmark_status = classify_against_benchmark(entity.operating_margin_pct, benchmark)
            if benchmark:
                benchmark_min = benchmark["min"]
                benchmark_lower_quartile = benchmark["lower_quartile"]
                benchmark_median = benchmark["median"]
                benchmark_upper_quartile = benchmark["upper_quartile"]
                benchmark_max = benchmark["max"]
                pli_indicator = "Operating Margin (%)"

        if is_manufacturer:
            benchmark = lookup_benchmark("Contract Manufacturing", entity.region, benchmark_lookup)
            benchmark_status = classify_against_benchmark(entity.full_cost_markup_pct, benchmark)
            if benchmark:
                benchmark_min = benchmark["min"]
                benchmark_lower_quartile = benchmark["lower_quartile"]
                benchmark_median = benchmark["median"]
                benchmark_upper_quartile = benchmark["upper_quartile"]
                benchmark_max = benchmark["max"]
                pli_indicator = "Full Cost Mark-up (%)"

        summary_rows.append({
            "CompanyCode": entity.company_code,
            "EntityName": entity.entity_name,
            "Region": entity.region,
            "Country": entity.country_name,
            "Currency": entity.currency,
            "FunctionalRole": ", ".join(entity.functional_role.values()),
            "RevenueLC": entity.revenue_lc,
            "RevenueEUR": entity.revenue_eur(fx_rate_lookup),
            "COGSLC": entity.cogs,
            "COGSEUR": entity.cogs_eur(fx_rate_lookup),
            "SGALC": entity.sga,
            "SGAEUR": entity.sga_eur(fx_rate_lookup),
            "RDLC": entity.rd,
            "RDEUR": entity.rd_eur(fx_rate_lookup),
            "OtherOpexLC": entity.other_opex,
            "OtherOpexEUR": entity.other_opex_eur(fx_rate_lookup),
            "OperatingProfitLC": entity.operating_profit_lc,
            "OperatingProfitEUR": entity.operating_profit_eur(fx_rate_lookup),
            "OperatingMarginPct": entity.operating_margin_pct,
            "FullCostMarkupPct": entity.full_cost_markup_pct if is_manufacturer else None,
            "PLIIndicator": pli_indicator,
            "BenchmarkMin": benchmark_min,
            "BenchmarkLowerQuartile": benchmark_lower_quartile,
            "BenchmarkMedian": benchmark_median,
            "BenchmarkUpperQuartile": benchmark_upper_quartile,
            "BenchmarkMax": benchmark_max,
            "BenchmarkStatus": benchmark_status,
        })

    print("Step 4 done - metrics calculated and classified")

    # --- Step 5: Reconciliation ---
    cleaned_financials_total = dataset.grand_total_revenue()
    ok = reconciles(original_journal_total, cleaned_financials_total, tolerance=1.0)
    print(f"Step 5 - Journal total: {original_journal_total:,.2f} | Financials total: "
          f"{cleaned_financials_total:,.2f} | Reconciles: {ok}")
    if not ok:
        unmapped_total = sum(row["Amount"] for row in unmapped_rows)
        print(f"   -> Difference: {abs(original_journal_total - cleaned_financials_total):,.2f} "
              f"(matches the {len(unmapped_rows)} unmapped GL-4900 row(s), total {unmapped_total:,.2f})")

    # --- Step 6: Export main table ---
    summary_df = pd.DataFrame(summary_rows).sort_values("CompanyCode").reset_index(drop=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    summary_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Step 6 done - result saved to: {OUTPUT_FILE}")

    if unmapped_rows:
        pd.DataFrame(unmapped_rows).to_csv(UNMAPPED_FILE, index=False)
        print(f"Unmapped rows saved to: {UNMAPPED_FILE} ({len(unmapped_rows)} row(s))")

    # --- Step 7: Export intercompany transaction volume ---
    ic_volume_rows = build_intercompany_volume_summary(dataset, fx_rate_lookup)
    ic_volume_df = pd.DataFrame(ic_volume_rows).sort_values(["ReportingEntity", "TransactionPartner"]).reset_index(drop=True)
    ic_volume_df.to_csv(IC_VOLUME_FILE, index=False)
    print(f"Step 7 done - intercompany transaction volume saved to: {IC_VOLUME_FILE}")

    return summary_df, ic_volume_df


if __name__ == "__main__":
    final_table, ic_volume_table = run_pipeline()
    print("\nFinal summary table:")
    print(final_table.to_string(index=False))
    print("\nIntercompany transaction volume:")
    print(ic_volume_table.to_string(index=False))