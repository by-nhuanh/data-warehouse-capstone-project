
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    sk_id_curr as unique_field,
    count(*) as n_records

from "credit_lakehouse"."gold"."fct_application_train"
where sk_id_curr is not null
group by sk_id_curr
having count(*) > 1



  
  
      
    ) dbt_internal_test