"""
data_io.py
--------------
Reads all 6 Excel source files used by the pipeline (ERP journal, entity
financials, GL account mapping, benchmark studies, entity master data,
and FX rates) and returns them as pandas DataFrames. Also provides a
generator that yields cleaned journal rows one at a time instead of
loading the full cleaned dataset into memory at once.
"""
import pandas as pd
from pathlib import Path

DATA_DIR=Path(__file__).resolve().parent.parent.parent / "data"

def read_erp_export(path: Path= DATA_DIR / "raw_erp_export.xlsx") -> pd.DataFrame:
  return pd.read_excel(path, sheet_name="Journal")

def read_benchmark_studies(path: Path= DATA_DIR / "benchmark_studies.xlsx") -> pd.DataFrame:
   return pd.read_excel(path,sheet_name="Benchmarks")

def read_entity_financials(path: Path= DATA_DIR / "entity_financials.xlsx") -> pd.DataFrame:
   return pd.read_excel(path,sheet_name="Financials")

def read_fx_rates(path: Path= DATA_DIR / "fx_rates.xlsx") -> pd.DataFrame:
   return pd.read_excel(path,sheet_name="FxRates")

def read_entity_master(path: Path= DATA_DIR / "entity_master.xlsx") -> pd.DataFrame:
   return pd.read_excel(path,sheet_name="EntityMaster")

def read_mapping_gl_accounts(path: Path= DATA_DIR / "mapping_gl_accounts.xlsx") -> pd.DataFrame:
   return pd.read_excel(path,sheet_name="Mapping")

if __name__ == "__main__":
    df = read_erp_export()
    print(df.shape)
    print(df.head(3))

    df = read_benchmark_studies()
    print(df.shape)
    print(df.head(3))

    df = read_entity_financials()
    print(df.shape)
    print(df.head(3))

    df = read_fx_rates()
    print(df.shape)
    print(df.head(3))

    df = read_entity_master()
    print(df.shape)
    print(df.head(3))

    df = read_mapping_gl_accounts()
    print(df.shape)
    print(df.head(3))