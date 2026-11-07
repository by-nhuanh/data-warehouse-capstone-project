
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select normalized_instalment_version
from "credit_lakehouse"."silver"."stg_installments_payments"
where normalized_instalment_version is null



  
  
      
    ) dbt_internal_test