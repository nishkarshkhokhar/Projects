import sqlite3
import pandas as pd
import re
from datetime import datetime, timedelta


# defining a few parameters
DB_PATH = "C:/Users/Nishkarsh Khokhar/Desktop/trading.db"
MAX_TRADE_AGE_DAYS = 360   # timeliness threshold, putting as 1 year data(taking 360 days as 1 year)
SECURITY_ID_PATTERN = r"^SEC_\d{4}$"


# Connecting to Database, please change directory as per where the file is stored
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# create an exceptions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS exceptions (
    ExceptionID INTEGER PRIMARY KEY AUTOINCREMENT,
    TradeID INTEGER,
    RuleViolated TEXT,
    Reason TEXT,
    DetectedAt TEXT
)
""")

conn.commit()

# uncomment below to clean exceptions table if any issue persists, this helps with if_exists = 'append' condition in to_sql as seen in write_exceptions()
# cursor.execute("DELETE FROM exceptions")
# conn.commit()


# Loading data

trades_df = pd.read_sql("SELECT * FROM Trades", conn)
securities_df = pd.read_sql("SELECT * FROM Securities", conn)

# -----------------------------
# Results container
# -----------------------------
# results list will contain all trades where an exception was caught
results = []

def log_check(check_name, failed_rows):
    results.append({
        "Check": check_name,
        "Failed_Rows": len(failed_rows),
        "Status": "FAIL" if len(failed_rows) > 0 else "PASS"
    })
    return failed_rows

from datetime import datetime


# this is to write exceptions to the new table
def write_exceptions(df, rule, reason):
    if df.empty:
        return

    exceptions_df = pd.DataFrame({
        "TradeID": df["TradeID"],
        "RuleViolated": rule,
        "Reason": reason,
        "DetectedAt": datetime.now().isoformat()
    })

    exceptions_df.to_sql(
        "exceptions",
        conn,
        if_exists="append",
        index=False
    )


# =====================================================
# COMPLETENESS CHECKS
# =====================================================

# trades table
critical_trade_fields = ["TradeID", "SecurityID", "Price", "Quantity", "Timestamp"]

missing_trades = trades_df[
    trades_df[critical_trade_fields].isnull().any(axis=1)
]

log_check("Completeness: NULLs in Trades", missing_trades)

write_exceptions(
    missing_trades,
    rule="Completeness",
    reason="Missing one or more critical fields"
)

# securities table(Note: securities table checks will be checked here, but not flowing to exceptions table as want to show bad tradeIDs, securities are non-unique by design)
missing_securities = securities_df[
    securities_df[["SecurityID", "SecurityType"]].isnull().any(axis=1)
]

log_check("Completeness: NULLs in Securities", missing_securities)

# write_exceptions(
#     missing_securities,
#     rule="Completeness",
#     reason="Missing one or more critical fields"
# )


# =====================================================
# ACCURACY CHECKS
# =====================================================
# trades table
invalid_price_qty = trades_df[(trades_df["Price"] <= 0) | (trades_df["Quantity"] <= 0)]

log_check("Accuracy: Non-positive Price or Quantity", invalid_price_qty)

write_exceptions(
    invalid_price_qty,
    rule="Accuracy",
    reason="Price or Quantity is non-positive"
)



# =====================================================
# TIMELINESS CHECKS
# =====================================================
trades_df["Timestamp"] = pd.to_datetime(trades_df["Timestamp"], errors="coerce")

cutoff_date = datetime.now() - timedelta(days=MAX_TRADE_AGE_DAYS)

stale_trades = trades_df[trades_df["Timestamp"] < cutoff_date]

log_check("Timeliness: Stale Trades", stale_trades)

write_exceptions(
    stale_trades,
    rule="Timeliness",
    reason="Trade timestamp older than allowed window"
)

# =====================================================
# VALIDITY CHECKS
# =====================================================
# trades table
invalid_security_id_format = trades_df[
    ~trades_df["SecurityID"].astype(str).str.match(SECURITY_ID_PATTERN)
]

log_check("Validity: Invalid SecurityID Format", invalid_security_id_format)

write_exceptions(
    invalid_security_id_format,
    rule="Validity",
    reason="SecurityID does not match expected pattern"
)

# Orphan trades (trade in trades table but not in securities)
orphan_trades = trades_df[~trades_df["SecurityID"].isin(securities_df["SecurityID"])]

log_check("Validity: Orphan Trades (No Security)", orphan_trades)

write_exceptions(
    orphan_trades,
    rule="Validity",
    reason="SecurityID not found in Securities table"
)


# securities table
invalid_security_id_sec = securities_df[~securities_df["SecurityID"].astype(str).str.match(SECURITY_ID_PATTERN)]

log_check("Validity: Invalid SecurityID Format (Securities)", invalid_security_id_sec)

# write_exceptions(
#     invalid_security_id_sec,
#     rule="Validity",
#     reason="SecurityID does not match expected pattern"
# )

ALLOWED_SECURITY_TYPES = [
    "Equity", "Fixed Income", "FX", "Derivative",  "ETF"
]


invalid_security_type = securities_df[
    ~securities_df["SecurityType"].isin(ALLOWED_SECURITY_TYPES)
]

log_check("Validity: Invalid SecurityType", invalid_security_type)

# write_exceptions(
#     invalid_security_type,
#     rule="Validity",
#     reason="Security Type is not an allowable type"
# )


# =====================================================
# Summary Report
# =====================================================
summary_df = pd.DataFrame(results)

print("\n=== DATA QUALITY SUMMARY ===")
print(summary_df)

# fail pipeline message if any critical checks fail
if (summary_df["Status"] == "FAIL").any():
    print("\n❌ Data quality checks failed.")
else:
    print("\n✅ All data quality checks passed.")



pd.read_sql(
    "SELECT * FROM exceptions ORDER BY DetectedAt DESC",
    conn
) 



# saving exceptions file to a csv

exceptions = pd.read_sql(
    "SELECT * FROM exceptions ORDER BY DetectedAt DESC",
    conn
)

exceptions.to_csv('C:/Users/Nishkarsh Khokhar/Desktop/exceptions.csv')

conn.close() 

