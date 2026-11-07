"""Read-only source adapter. Local views live only in an in-memory database."""
from pathlib import Path
import duckdb, json

def connect(root):
    root=Path(root).resolve()
    c=duckdb.connect(':memory:')
    c.execute("SET threads=4")
    availability={}
    manifest = root / "data" / "manifests" / "latest.json"
    if not manifest.is_file():
        raise FileNotFoundError(
            f"Khong tim thay file manifest: {manifest}"
        )
    with manifest.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    entries = manifest_data.get("sources", [])
    if len(entries) != 8:
        raise ValueError(
            f"Manifest phai co 8 nguon, hien co {len(entries)}"
        )
    for e in entries:
        name=e['duckdb_relation'].split('.')[-1]
        p=root/e['parquet']
        raw=root/'data/raw'/e['file']
        if p.exists():
            expr="read_parquet(?)"; source=p
        elif raw.exists():
            expr="read_csv_auto(?, sample_size=20480)"; source=raw
        else:
            availability[name]={'status':'MISSING','expected':str(p)}; continue
        # CREATE VIEW cannot accept prepared parameters. Quote trusted filesystem paths.
        literal="'"+str(source).replace("'","''")+"'"
        relation=expr.replace("?",literal)
        columns=c.execute(f'DESCRIBE SELECT * FROM {relation}').fetchall()
        numeric={'SK_ID_CURR','SK_ID_PREV','SK_ID_BUREAU','TARGET','NUM_INSTALMENT_VERSION','NUM_INSTALMENT_NUMBER','MONTHS_BALANCE'}
        projection=[]
        for col,*_ in columns:
            if col in numeric or col.startswith(('AMT_','DAYS_')):
                dtype='BIGINT' if col in numeric else 'DOUBLE'
                projection.append(f'try_cast("{col}" as {dtype}) as "{col}"')
            else: projection.append(f'"{col}"')
        c.execute(f'CREATE VIEW "{name}" AS SELECT '+','.join(projection)+f' FROM {relation}')
        availability[name]={'status':'READY','source':str(source)}
    db=root/'database/credit_lakehouse.duckdb'
    if db.exists():
        c.execute("ATTACH '"+str(db).replace("'","''")+"' AS original (READ_ONLY)")
    missing_sources = [
        name
        for name, info in availability.items()
        if info["status"] == "MISSING"
    ]
    if missing_sources:
        raise FileNotFoundError(
            "Thieu du lieu cho dashboard: "
            + ", ".join(missing_sources)
        )
    return c, availability

def query(c,sql,params=None):
    return c.execute(sql,params or []).fetchdf()

def application_sql(availability):
    cols='SK_ID_CURR,TARGET,NAME_CONTRACT_TYPE,NAME_EDUCATION_TYPE,AMT_INCOME_TOTAL,AMT_CREDIT,AMT_ANNUITY,AMT_GOODS_PRICE,DAYS_BIRTH'
    train=f"select {cols}, 'Train' as dataset from application_train"
    test=f"select {cols.replace('TARGET,','NULL::INTEGER AS TARGET,')}, 'Test' as dataset from application_test"
    return train+(' union all '+test if 'application_test' in availability and availability['application_test']['status']=='READY' else '')

PERIOD_SQL="""
select SK_ID_CURR,SK_ID_PREV,NUM_INSTALMENT_VERSION,NUM_INSTALMENT_NUMBER,
max(AMT_INSTALMENT) due,sum(AMT_PAYMENT) paid,
max(DAYS_ENTRY_PAYMENT)-max(DAYS_INSTALMENT) delta,
count(*) rows_count,count(DAYS_ENTRY_PAYMENT) valid_dates,
case when count(AMT_PAYMENT)=count(*) and count(AMT_INSTALMENT)=count(*)
then greatest(max(AMT_INSTALMENT)-sum(AMT_PAYMENT),0) end shortfall
from installments_payments
where SK_ID_CURR is not null and SK_ID_PREV is not null
and NUM_INSTALMENT_VERSION is not null and NUM_INSTALMENT_NUMBER is not null
 group by 1,2,3,4
"""
