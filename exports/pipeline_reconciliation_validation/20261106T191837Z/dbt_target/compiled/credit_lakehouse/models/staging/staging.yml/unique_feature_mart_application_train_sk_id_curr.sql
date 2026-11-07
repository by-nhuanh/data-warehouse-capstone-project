
    
    

select
    sk_id_curr as unique_field,
    count(*) as n_records

from "credit_lakehouse"."gold"."feature_mart_application_train"
where sk_id_curr is not null
group by sk_id_curr
having count(*) > 1


