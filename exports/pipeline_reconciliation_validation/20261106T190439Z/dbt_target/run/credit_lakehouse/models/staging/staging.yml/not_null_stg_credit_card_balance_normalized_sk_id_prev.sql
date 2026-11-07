
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select normalized_sk_id_prev
from "credit_lakehouse"."silver"."stg_credit_card_balance"
where normalized_sk_id_prev is null



  
  
      
    ) dbt_internal_test