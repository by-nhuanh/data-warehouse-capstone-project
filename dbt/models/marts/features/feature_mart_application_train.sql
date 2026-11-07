select
    *,
    case when amt_income_total > 0 then amt_credit / amt_income_total end as credit_to_income,
    case when amt_income_total > 0 then amt_annuity / amt_income_total end as annuity_to_income,
    case when amt_goods_price > 0 then amt_credit / amt_goods_price end as credit_to_goods_price,
    case when cnt_fam_members > 0 then amt_income_total / cnt_fam_members end as income_per_family_member,
    case when cleaned_days_employed is not null
         then abs(cleaned_days_employed) / 365.25 end as employment_years
from {{ ref('int_application_train_prep') }}
