
    
    

with all_values as (

    select
        STATUS_DPD as value_field,
        count(*) as n_records

    from "credit_lakehouse"."silver"."stg_bureau_balance"
    group by STATUS_DPD

)

select *
from all_values
where value_field not in (
    '0','1','2','3','4','5'
)


