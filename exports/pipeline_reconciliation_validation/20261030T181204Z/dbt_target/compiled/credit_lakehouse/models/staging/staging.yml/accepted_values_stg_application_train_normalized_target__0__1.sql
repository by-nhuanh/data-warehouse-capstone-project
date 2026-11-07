
    
    

with all_values as (

    select
        normalized_target as value_field,
        count(*) as n_records

    from "credit_lakehouse"."silver"."stg_application_train"
    group by normalized_target

)

select *
from all_values
where value_field not in (
    '0','1'
)


