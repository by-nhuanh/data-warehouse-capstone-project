
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select STATUS
from "credit_lakehouse"."silver"."stg_bureau_balance"
where STATUS is null



  
  
      
    ) dbt_internal_test