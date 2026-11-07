
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select normalized_months_balance
from "credit_lakehouse"."silver"."stg_credit_card_balance"
where normalized_months_balance is null



  
  
      
    ) dbt_internal_test