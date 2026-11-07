
  
  create view "credit_lakehouse"."silver"."stg_pos_cash_balance__dbt_tmp" as (
    select
    *,
    try_cast(SK_ID_CURR as bigint) as normalized_sk_id_curr,
    try_cast(SK_ID_PREV as bigint) as normalized_sk_id_prev,
    try_cast(MONTHS_BALANCE as integer) as normalized_months_balance,
    try_cast(SK_DPD as integer) as normalized_sk_dpd,
    try_cast(SK_DPD_DEF as integer) as normalized_sk_dpd_def
from "credit_lakehouse"."bronze"."pos_cash_balance"
  );
