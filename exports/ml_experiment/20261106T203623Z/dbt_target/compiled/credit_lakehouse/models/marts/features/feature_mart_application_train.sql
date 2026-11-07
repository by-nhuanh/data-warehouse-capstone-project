select
    *,
    case when amt_income_total > 0 then amt_credit / amt_income_total end as credit_to_income,
    case when amt_income_total > 0 then amt_annuity / amt_income_total end as annuity_to_income
from "credit_lakehouse"."silver"."int_application_train_prep"