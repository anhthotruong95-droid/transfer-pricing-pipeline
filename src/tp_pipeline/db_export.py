"""
db_export.py
----------------
Loads the pipeline's 3 output CSVs into a SQLite database for further
SQL-based analysis. Uses a "full refresh" pattern - consistent with the
rest of the pipeline, the database is dropped and rebuilt from scratch
on every run, not incrementally updated.
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
DB_FILE = OUTPUT_DIR / "tp_pipeline.db"

FINANCIALS_FILE = OUTPUT_DIR / "financial_statements.csv"
IC_VOLUME_FILE = OUTPUT_DIR / "intercompany_transaction_volume.csv"
UNMAPPED_FILE = OUTPUT_DIR / "unmapped_transactions.csv"


CREATE_FINANCIAL_STATEMENTS = """
CREATE TABLE financial_statements (
    CompanyCode TEXT PRIMARY KEY,
    EntityName TEXT,
    Region TEXT,
    Country TEXT,
    Currency TEXT,
    FunctionalRole TEXT,
    RevenueLC REAL,
    RevenueEUR REAL,
    COGSLC REAL,
    COGSEUR REAL,
    SGALC REAL,
    SGAEUR REAL,
    RDLC REAL,
    RDEUR REAL,
    OtherOpexLC REAL,
    OtherOpexEUR REAL,
    OperatingProfitLC REAL,
    OperatingProfitEUR REAL,
    OperatingMarginPct REAL,
    FullCostMarkupPct REAL,
    PLIIndicator TEXT,
    BenchmarkMin REAL,
    BenchmarkLowerQuartile REAL,
    BenchmarkMedian REAL,
    BenchmarkUpperQuartile REAL,
    BenchmarkMax REAL,
    BenchmarkStatus TEXT
);
"""

CREATE_IC_VOLUME = """
CREATE TABLE intercompany_transaction_volume (
    ReportingEntity TEXT,
    RoleOfReportingEntity TEXT,
    TransactionPartner TEXT,
    RoleOfTransactionPartner TEXT,
    TransactionGroup TEXT,
    Currency TEXT,
    TotalAmountLC REAL,
    TotalAmountEUR REAL
);
"""

CREATE_UNMAPPED = """
CREATE TABLE unmapped_transactions (
    TransactionID TEXT,
    PostingDate TEXT,
    BookingText TEXT,
    CompanyCode TEXT,
    PartnerCompanyCode TEXT,
    GLAccount TEXT,
    TransactionType TEXT,
    Amount REAL,
    Currency TEXT,
    error TEXT
);
"""


def build_database():
    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(CREATE_FINANCIAL_STATEMENTS)
    cursor.execute(CREATE_IC_VOLUME)
    cursor.execute(CREATE_UNMAPPED)
    conn.commit()

    financials_df = pd.read_csv(FINANCIALS_FILE)
    financials_df.to_sql("financial_statements", conn, if_exists="append", index=False)

    ic_volume_df = pd.read_csv(IC_VOLUME_FILE)
    ic_volume_df.to_sql("intercompany_transaction_volume", conn, if_exists="append", index=False)

    unmapped_df = pd.read_csv(UNMAPPED_FILE)
    unmapped_df.to_sql("unmapped_transactions", conn, if_exists="append", index=False)

    conn.close()
    print(f"Database rebuilt: {DB_FILE}")
    print(f"  - financial_statements: {len(financials_df)} rows")
    print(f"  - intercompany_transaction_volume: {len(ic_volume_df)} rows")
    print(f"  - unmapped_transactions: {len(unmapped_df)} rows")


if __name__ == "__main__":
    build_database()