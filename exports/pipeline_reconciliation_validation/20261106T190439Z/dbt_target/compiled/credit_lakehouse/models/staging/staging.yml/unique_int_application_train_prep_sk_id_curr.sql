
    
    

select
    sk_id_curr as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."int_application_train_prep"
where sk_id_curr is not null
group by sk_id_curr
having count(*) > 1


