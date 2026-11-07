
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sk_id_curr
from "credit_lakehouse"."silver"."int_application_train_prep"
where sk_id_curr is null



  
  
      
    ) dbt_internal_test