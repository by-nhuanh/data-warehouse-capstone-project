select
    normalized_sk_id_curr as sk_id_curr,
    normalized_target as target,
    normalized_amt_credit as amt_credit,
    normalized_amt_income_total as amt_income_total,
    normalized_amt_annuity as amt_annuity,
    derived_age_years as age_years,
    cleaned_days_employed,
    flag_days_employed_anomaly,
    CODE_GENDER as code_gender,
    NAME_CONTRACT_TYPE as name_contract_type,
    cast(SK_ID_CURR as varchar) as source_sk_id_curr
from "credit_lakehouse"."silver"."stg_application_train"