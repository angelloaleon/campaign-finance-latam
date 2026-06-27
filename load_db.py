"""
load_db.py
Loads the project CSVs into an in-memory SQLite database and runs queries.sql,
printing each query's results. Requires only the Python standard library + pandas.

Usage:
    python load_db.py
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
CFRS_PATH = ROOT / "data" / "processed" / "cfrs_scores.csv"
CPI_PATH  = ROOT / "data" / "raw" / "CPI2025_Results.csv"
SQL_PATH  = ROOT / "queries.sql"

# --- Load CSVs ---
cfrs = pd.read_csv(CFRS_PATH)

cpi = pd.read_csv(CPI_PATH)
cpi = cpi[cpi["Region"] == "AME"][["Country / Territory", "ISO3", "CPI 2025 score"]].copy()
cpi.columns = ["Country_CPI", "ISO3", "cpi_2025"]
cpi["cpi_2025"] = pd.to_numeric(cpi["cpi_2025"], errors="coerce")

# --- Build SQLite database ---
con = sqlite3.connect(":memory:")
cfrs.to_sql("cfrs", con, index=False, if_exists="replace")
cpi.to_sql("cpi", con, index=False, if_exists="replace")

# --- Run each query in queries.sql, printing results ---
sql_text = SQL_PATH.read_text(encoding="utf-8")
# split on blank-line-separated statements that start with SELECT
statements = [s.strip() for s in sql_text.split(";") if s.strip() and "SELECT" in s.upper()]

for i, stmt in enumerate(statements, 1):
    # grab the comment header line for a label, if present
    label = next((ln.strip("- ").strip() for ln in stmt.splitlines()
                  if ln.strip().startswith("-- Query")), f"Query {i}")
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    print(pd.read_sql_query(stmt + ";", con).to_string(index=False))

con.close()
