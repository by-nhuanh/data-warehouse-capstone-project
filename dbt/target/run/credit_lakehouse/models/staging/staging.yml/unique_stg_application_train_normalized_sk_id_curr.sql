
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    normalized_sk_id_curr as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."stg_application_train"
where normalized_sk_id_curr is not null
group by normalized_sk_id_curr
having count(*) > 1



  
  
      
    ) dbt_internal_test