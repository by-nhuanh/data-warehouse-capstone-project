
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select normalized_sk_id_bureau
from "credit_lakehouse"."silver"."stg_bureau"
where normalized_sk_id_bureau is null



  
  
      
    ) dbt_internal_test