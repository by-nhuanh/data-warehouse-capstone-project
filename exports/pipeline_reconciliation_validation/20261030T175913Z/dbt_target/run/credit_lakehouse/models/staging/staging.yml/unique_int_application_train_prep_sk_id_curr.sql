
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    sk_id_curr as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."int_application_train_prep"
where sk_id_curr is not null
group by sk_id_curr
having count(*) > 1



  
  
      
    ) dbt_internal_test