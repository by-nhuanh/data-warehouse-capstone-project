
    
    

select
    normalized_sk_id_bureau as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."stg_bureau"
where normalized_sk_id_bureau is not null
group by normalized_sk_id_bureau
having count(*) > 1


