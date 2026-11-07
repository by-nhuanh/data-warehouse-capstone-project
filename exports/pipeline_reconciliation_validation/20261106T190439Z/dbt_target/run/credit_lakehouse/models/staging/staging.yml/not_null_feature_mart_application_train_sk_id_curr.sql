
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sk_id_curr
from "credit_lakehouse"."gold"."feature_mart_application_train"
where sk_id_curr is null



  
  
      
    ) dbt_internal_test