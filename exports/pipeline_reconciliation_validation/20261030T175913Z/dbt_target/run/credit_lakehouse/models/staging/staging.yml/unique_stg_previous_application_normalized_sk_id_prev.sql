
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    normalized_sk_id_prev as unique_field,
    count(*) as n_records

from "credit_lakehouse"."silver"."stg_previous_application"
where normalized_sk_id_prev is not null
group by normalized_sk_id_prev
having count(*) > 1



  
  
      
    ) dbt_internal_test