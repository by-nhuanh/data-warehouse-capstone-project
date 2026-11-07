select
    *,
    try_cast(SK_ID_CURR as bigint) as normalized_sk_id_curr,
    try_cast(TARGET as integer) as normalized_target,
    try_cast(AMT_CREDIT as double) as normalized_amt_credit,
    try_cast(AMT_INCOME_TOTAL as double) as normalized_amt_income_total,
    try_cast(AMT_ANNUITY as double) as normalized_amt_annuity,
    case when try_cast(AMT_CREDIT as double) is null or try_cast(AMT_CREDIT as double) <= 0 then 1 else 0 end as flag_amt_credit_nonpositive_or_invalid,
    case when try_cast(AMT_INCOME_TOTAL as double) is null or try_cast(AMT_INCOME_TOTAL as double) <= 0 then 1 else 0 end as flag_amt_income_nonpositive_or_invalid,
    try_cast(DAYS_BIRTH as integer) as source_days_birth_integer,
    case when try_cast(DAYS_BIRTH as integer) is not null
         then cast(abs(try_cast(DAYS_BIRTH as integer)) / 365.25 as integer) end as derived_age_years,
    try_cast(DAYS_EMPLOYED as integer) as source_days_employed_integer,
    case when try_cast(DAYS_EMPLOYED as integer) = 365243 then null
         else try_cast(DAYS_EMPLOYED as integer) end as cleaned_days_employed,
    case when try_cast(DAYS_EMPLOYED as integer) = 365243 then 1 else 0 end as flag_days_employed_anomaly
from "credit_lakehouse"."bronze"."application_train"