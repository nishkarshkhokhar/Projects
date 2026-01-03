# Data Quality Documentation

## 1. Data Dictionary

### 1.1 Trades Table (Raw Data)

| Field Name | Data Type           | Description                                                         |
| ---------- | ------------------- | ------------------------------------------------------------------- |
| TradeID    | INTEGER             | Unique identifier for each trade. Primary key.                      |
| SecurityID | TEXT                | Identifier of the traded security. Foreign key to Securities table. |
| Price      | REAL                | Execution price of the trade. Expected to be positive.              |
| Quantity   | INTEGER             | Number of units traded. Expected to be positive.                    |
| Timestamp  | TEXT (ISO datetime) | Time when the trade was executed. Used for timeliness checks.       |

---

### 1.2 Securities Table (Reference / Master Data)

| Field Name   | Data Type | Description                                                     |
| ------------ | --------- | --------------------------------------------------------------- |
| SecurityID   | TEXT      | Unique identifier for a security (e.g., SEC_0001). Primary key. |
| SecurityType | TEXT      | Asset class or instrument type (e.g., Equity, FX, ETF).         |

---

### 1.3 Exceptions Table (`exceptions`)

| Field Name   | Data Type           | Description                                                               |
| ------------ | ------------------- | ------------------------------------------------------------------------- |
| ExceptionID  | INTEGER             | Auto-incremented unique identifier for each exception.                    |
| TradeID      | INTEGER             | TradeID associated with the exception (NULL for security-level issues).   |
| RuleViolated | TEXT                | Name of the data quality rule that failed (Completeness, Accuracy, etc.). |
| Reason       | TEXT                | Human-readable explanation of why the record failed the check.            |
| DetectedAt   | TEXT (ISO datetime) | Timestamp when the exception was detected.                                |

---

## 2. Data Lineage

### 2.1 High-Level Flow

1. **Mock Data Generation**

   * Trades dataset and Securities dataset are generated using Python.
   * Data includes intentional edge cases (nulls, negatives, format issues).

2. **Data Storage (SQLite Database)**

   * Trades data loaded into `Trades` table.
   * Securities data loaded into `Securities` table.

3. **Data Quality Checks (`data_quality.py`)**

   * Python script reads data from `Trades` and `Securities` tables.
   * Quality checks executed across four dimensions:

     * Completeness (NULL checks)
     * Accuracy (business rules like positive price/quantity)
     * Timeliness (timestamp within allowed window)
     * Validity (format checks, referential integrity)

4. **Exception Logging**

   * Records failing any check are written to the `exceptions` table.
   * Each row captures the TradeID (if applicable), rule violated, reason, and detection timestamp.

5. **Downstream Usage (Future)**

   * Exceptions table can be used for:

     * Auditing and reporting
     * Data remediation workflows
     * Monitoring data quality trends over time

---

### 2.2 Text-Based Lineage Diagram

```
Mock Data (Python)
   │
   ▼
SQLite Database
   ├── Trades
   └── Securities
        │
        ▼
Data Quality Script (data_quality.py)
   │  ├── Completeness Checks
   │  ├── Accuracy Checks
   │  ├── Timeliness Checks
   │  └── Validity Checks
   ▼
Exceptions Table (exceptions)
```

---

## Summary

This documentation describes the structure of the raw data, the data quality exceptions table, and the end-to-end lineage from data generation to automated quality validation. It is designed to support auditability, explainability, and future extensibility of the data quality framework.

Pleased find the Tableau dashboard corresponding to the exceptions logged on this link: https://public.tableau.com/app/profile/nishkarsh.khokhar/viz/DataQualitydashboard-TradesSecurities/DQDashboardforTrades
