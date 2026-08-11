"""
lookups.py
--------------
Builds fast in-memory lookups from the mapping and master data files:
GL account -> transaction group, transaction group/region -> benchmark
study, company code -> entity master data, and currency -> EUR exchange
rate.
"""


def build_benchmark_lookup(benchmark_df):
    """Builds a (transaction group, region) -> benchmark details lookup."""
    lookup = {}
    for index, row in benchmark_df.iterrows():
        key = (row["TransactionGroup"], row["Region"])
        lookup[key] = {
            "min": row["Min"],
            "lower_quartile": row["LowerQuartile"],
            "median": row["Median"],
            "upper_quartile": row["UpperQuartile"],
            "max": row["Max"],
            "year": row["Year"]
        }
    return lookup


def build_gl_account_mapping_lookup(mapping_df):
    """Builds a GL account -> transaction group lookup."""
    lookup = {}
    for index, row in mapping_df.iterrows():
        key = str(row["GLAccount"])
        lookup[key] = row["TransactionGroup"]
    return lookup


def build_entity_master_lookup(master_df):
    """Builds a company code -> entity master data lookup."""
    lookup = {}
    for index, row in master_df.iterrows():
        key = row["CompanyCode"]
        lookup[key] = {
            "legal_entity_name": row["LegalEntityName"],
            "country_iso": row["CountryISO"],
            "country_name": row["CountryName"],
            "region": row["Region"],
            "currency": row["Currency"],
        }
    return lookup


def build_fx_rate_lookup(fx_df):
    """Builds a currency -> EUR exchange rate lookup."""
    lookup = {}
    for index, row in fx_df.iterrows():
        key = row["Currency"]
        lookup[key] = row["RateToEUR"]
    return lookup


def lookup_benchmark(transaction_group, region, benchmark_lookup):
    """Looks up a benchmark by (transaction group, region)."""
    return benchmark_lookup.get((transaction_group, region))


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tp_pipeline.data_io import read_benchmark_studies, read_mapping_gl_accounts, read_fx_rates, read_entity_master

    print(build_gl_account_mapping_lookup(read_mapping_gl_accounts()))
    print(build_entity_master_lookup(read_entity_master())["US02"])
    print(build_fx_rate_lookup(read_fx_rates()))
    benchmark_lookup = build_benchmark_lookup(read_benchmark_studies())