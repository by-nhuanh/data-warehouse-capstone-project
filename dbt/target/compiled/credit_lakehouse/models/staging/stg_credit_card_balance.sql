select
    *,
    try_cast(SK_ID_CURR as bigint) as normalized_sk_id_curr,
    try_cast(SK_ID_PREV as bigint) as normalized_sk_id_prev,
    try_cast(MONTHS_BALANCE as integer) as normalized_months_balance,
    try_cast(AMT_BALANCE as double) as normalized_amt_balance,
    try_cast(AMT_CREDIT_LIMIT_ACTUAL as double) as normalized_amt_credit_limit_actual,
    case when try_cast(AMT_CREDIT_LIMIT_ACTUAL as double) > 0
         then try_cast(AMT_BALANCE as double) / try_cast(AMT_CREDIT_LIMIT_ACTUAL as double) end as derived_credit_utilization
from "credit_lakehouse"."bronze"."credit_card_balance"