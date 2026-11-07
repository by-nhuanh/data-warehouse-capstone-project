select
    *,
    try_cast(SK_ID_CURR as bigint) as normalized_sk_id_curr,
    try_cast(SK_ID_BUREAU as bigint) as normalized_sk_id_bureau,
    try_cast(AMT_ANNUITY as double) as normalized_amt_annuity,
    case when AMT_ANNUITY is null or trim(AMT_ANNUITY) = '' then 1 else 0 end as flag_amt_annuity_missing
from "credit_lakehouse"."bronze"."bureau"