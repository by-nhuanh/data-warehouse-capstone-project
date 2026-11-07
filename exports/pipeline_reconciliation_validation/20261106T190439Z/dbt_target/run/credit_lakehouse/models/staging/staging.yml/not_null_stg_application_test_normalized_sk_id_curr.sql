
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select normalized_sk_id_curr
from "credit_lakehouse"."silver"."stg_application_test"
where normalized_sk_id_curr is null



  
  
      
    ) dbt_internal_test