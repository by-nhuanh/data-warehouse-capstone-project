select
    *,
    try_cast(SK_ID_CURR as bigint) as normalized_sk_id_curr,
    try_cast(SK_ID_PREV as bigint) as normalized_sk_id_prev,
    try_cast(NUM_INSTALMENT_VERSION as integer) as normalized_instalment_version,
    try_cast(NUM_INSTALMENT_NUMBER as integer) as normalized_instalment_number,
    try_cast(DAYS_INSTALMENT as double) as normalized_days_instalment,
    try_cast(DAYS_ENTRY_PAYMENT as double) as normalized_days_entry_payment,
    try_cast(AMT_INSTALMENT as double) as normalized_amt_instalment,
    try_cast(AMT_PAYMENT as decimal(20,4)) as normalized_amt_payment,
    case when DAYS_ENTRY_PAYMENT is null or trim(DAYS_ENTRY_PAYMENT) = '' then 1 else 0 end as flag_unpaid_installment,
    case when DAYS_ENTRY_PAYMENT is null or trim(DAYS_ENTRY_PAYMENT) = '' then null
         else greatest(0, try_cast(DAYS_ENTRY_PAYMENT as double) - try_cast(DAYS_INSTALMENT as double)) end as derived_dpd_installment
from "credit_lakehouse"."bronze"."installments_payments"