# DTWH — Home Credit Risk Dashboard

Streamlit dashboard for Home Credit application risk and credit history.

## Run locally

```bash
pip install -r bi/streamlit/requirements.txt
streamlit run bi/streamlit/app.py
```

## Streamlit Community Cloud

**Live dashboard:** [Open DTWH Credit Risk Dashboard](https://dtwh-credit-risk.streamlit.app/)

- Repository: `by-nhuanh/data-warehouse-capstone-project`
- Main file: `bi/streamlit/app.py`
- Data: `data/bi_serving/*.parquet`
- Theme: `.streamlit/config.toml`

Both dashboards query read-only aggregated Parquet marts using DuckDB. They do not require Google Colab or Google Drive at viewing time.

## Data and metric scope

Application TARGET metrics use labeled Train records, excluding unlabeled Test records from the denominator. The Bureau chart compares individual monthly status counts and shares in all recorded states (0–5, C, X). Bureau monthly data does not preserve customer-cohort filtering and is hidden whenever that filtering is active.

The full capstone project, including notebooks, dbt models, source files, exports, and evidence, is preserved in the `archive/full-capstone` branch.

Do not upload credentials, private keys, or personal records to this public repository.
