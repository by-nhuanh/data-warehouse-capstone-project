
  
    
    

    create  table
      "credit_lakehouse"."gold"."fct_application_train__dbt_tmp"
  
    as (
      select * from "credit_lakehouse"."silver"."int_application_train_prep"
    );
  
  