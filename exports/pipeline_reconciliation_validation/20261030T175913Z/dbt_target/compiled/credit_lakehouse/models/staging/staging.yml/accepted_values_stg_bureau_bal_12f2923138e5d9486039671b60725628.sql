
    
    

with all_values as (

    select
        STATUS as value_field,
        count(*) as n_records

    from "credit_lakehouse"."silver"."stg_bureau_balance"
    group by STATUS

)

select *
from all_values
where value_field not in (
    'C','0','1','2','3','4','5','X'
)


