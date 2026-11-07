
  
  create view "credit_lakehouse"."silver"."stg_previous_application__dbt_tmp" as (
    select
    * exclude (RATE_INTEREST_PRIMARY),
    try_cast(SK_ID_CURR as bigint) as normalized_sk_id_curr,
    try_cast(SK_ID_PREV as bigint) as normalized_sk_id_prev,
    try_cast(AMT_CREDIT as double) as normalized_amt_credit,
    try_cast(AMT_ANNUITY as double) as normalized_amt_annuity
from "credit_lakehouse"."bronze"."previous_application"
  );
