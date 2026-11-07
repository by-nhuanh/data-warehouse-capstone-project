
    
    

select
    normalized_sk_id_curr as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."stg_application_test"
where normalized_sk_id_curr is not null
group by normalized_sk_id_curr
having count(*) > 1


