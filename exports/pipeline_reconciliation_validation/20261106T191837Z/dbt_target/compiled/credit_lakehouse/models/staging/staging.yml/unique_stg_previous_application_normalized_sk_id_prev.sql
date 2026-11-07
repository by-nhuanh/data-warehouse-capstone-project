
    
    

select
    normalized_sk_id_prev as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."stg_previous_application"
where normalized_sk_id_prev is not null
group by normalized_sk_id_prev
having count(*) > 1


