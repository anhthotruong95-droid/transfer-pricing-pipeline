"""
run_queries.py
------------------
SQL queries against the pipeline's SQLite database: benchmark outliers,
margin by region, intercompany volume by group and partner, and a
region-ranked margin comparison.

Run db_export.py first to make sure the database is up to date.
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_FILE = Path(__file__).resolve().parent.parent.parent / "output" / "tp_pipeline.db"


def run(conn, title, query):
    print(f"\n--- {title} ---")
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))


def main():
    conn = sqlite3.connect(DB_FILE)

    run(conn, "1. Entities Out of Range (filter + sort)", """
        SELECT CompanyCode, EntityName, Region, OperatingMarginPct, BenchmarkLowerQuartile, BenchmarkMedian, BenchmarkUpperQuartile, BenchmarkStatus
        FROM financial_statements
        WHERE BenchmarkStatus = 'Out of Range'
        ORDER BY OperatingMarginPct ASC;
    """)

    run(conn, "2. Average Operating Margin by Region (aggregation)", """
        SELECT Region, ROUND(AVG(OperatingMarginPct), 2) AS AvgOperatingMarginPct, COUNT(*) AS NumEntities
        FROM financial_statements
        WHERE FunctionalRole = 'Distributor'
        GROUP BY Region
        ORDER BY AvgOperatingMarginPct DESC;
    """)

    run(conn, "3. Intercompany volume with partner margin (join)", """
        SELECT
            v.ReportingEntity,
            v.RoleofReportingEntity,
            f.EntityName,
            v.TransactionPartner,
            v.TransactionGroup,
            f.OperatingMarginPct
        FROM intercompany_transaction_volume v
        LEFT JOIN financial_statements f ON v.TransactionPartner = f.CompanyCode
        WHERE v.TransactionGroup='Distribution';
    """)

    run(conn, "4. Total IC volume by transaction group (group by)", """
        SELECT TransactionGroup, ROUND(SUM(TotalAmountEUR), 2) AS TotalVolumeEUR
        FROM intercompany_transaction_volume
        GROUP BY TransactionGroup
        ORDER BY TotalVolumeEUR DESC;
    """)

    run(conn, "5. Rank distributors by IC volume within their region (window function)", """
        SELECT
            v.TransactionPartner,
            f.Region,
            v.TotalAmountEUR,
            RANK() OVER (PARTITION BY Region ORDER BY TotalAmountEUR DESC) AS RegionRank
        FROM intercompany_transaction_volume v
        LEFT JOIN financial_statements f ON v.TransactionPartner=f.CompanyCode
        WHERE TransactionGroup='Distribution'
        ORDER BY Region, RegionRank;
    """)

    run(conn, "6. Unmapped transaction total by company (aggregation)", """
        SELECT CompanyCode, COUNT(*) AS NumUnmappedRows, ROUND(SUM(Amount), 2) AS TotalUnmappedAmount
        FROM unmapped_transactions
        GROUP BY CompanyCode
        ORDER BY TotalUnmappedAmount DESC;
    """)

    conn.close()


if __name__ == "__main__":
    main()