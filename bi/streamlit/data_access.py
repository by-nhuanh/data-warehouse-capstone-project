from pathlib import Path
import duckdb

FILES = {
    "application_dashboard": "application_dashboard.parquet",
    "target_by_income": "target_by_income.parquet",
    "installments_customer_window": "installments_customer_window.parquet",
    "previous_contract_bridge": "previous_contract_bridge.parquet",
    "previous_customer_window": "previous_customer_window.parquet",
    "credit_card_customer_window": "credit_card_customer_window.parquet",
    "bureau_customer_debt": "bureau_customer_debt.parquet",
    "bureau_month_status": "bureau_month_status.parquet",
}

REQUIRED_COLUMNS = {
    "application_dashboard": [
        "SK_ID_CURR", "TARGET", "dataset",
        "NAME_CONTRACT_TYPE", "NAME_EDUCATION_TYPE",
        "AMT_INCOME_TOTAL", "cti", "credit_goods",
        "dti", "age_group"
    ],
    "target_by_income": [
        "income_group", "total_records",
        "target_1", "target_rate_pct"
    ],
    "installments_customer_window": [
        "SK_ID_CURR", "window_months", "periods",
        "valid_periods", "late_periods", "max_delta",
        "shortfall_sum"
    ],
    "previous_contract_bridge": [
        "SK_ID_CURR", "NAME_CONTRACT_TYPE"
    ],
    "previous_customer_window": [
        "SK_ID_CURR", "window_months",
        "previous_applications", "approved_applications"
    ],
    "credit_card_customer_window": [
        "SK_ID_CURR", "window_months", "utilization"
    ],
    "bureau_customer_debt": [
        "SK_ID_CURR", "bureau_debt_sum"
    ],
    "bureau_month_status": [
        "MONTHS_BALANCE", "STATUS", "records"
    ],
}


def connect(root):
    root = Path(root).resolve()
    folder = root / "data" / "bi_serving"

    missing = [
        filename
        for filename in FILES.values()
        if not (folder / filename).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            "Thieu file BI Serving: " + ", ".join(missing)
        )

    con = duckdb.connect(":memory:")
    con.execute("SET threads=2")
    con.execute("SET memory_limit='768MB'")

    available = {}

    for name, filename in FILES.items():
        path = folder / filename
        path_sql = str(path).replace("'", "''")

        con.execute(
            f'CREATE VIEW "{name}" AS '
            f"SELECT * FROM read_parquet('{path_sql}')"
        )

        actual_columns = {
            row[0]
            for row in con.execute(
                f'DESCRIBE SELECT * FROM "{name}"'
            ).fetchall()
        }

        absent = set(REQUIRED_COLUMNS[name]) - actual_columns

        if absent:
            raise ValueError(
                f"{filename} thieu cot: "
                + ", ".join(sorted(absent))
            )

        available[name] = {
            "status": "READY",
            "size_mb": round(
                path.stat().st_size / (1024 ** 2), 2
            )
        }

    return con, available


def query(con, sql, params=None):
    return con.execute(sql, params or []).fetchdf()


def scalar(con, sql, params=None):
    row = con.execute(sql, params or []).fetchone()
    return row[0] if row else None
