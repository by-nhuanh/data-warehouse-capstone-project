select *
from "credit_lakehouse"."silver"."stg_bureau_balance"
where
    (
        STATUS = 'C'
        and (
            STATUS_DPD is not null
            or IS_CLOSED is distinct from 1
            or IS_UNKNOWN is distinct from 0
        )
    )
    or (
        STATUS = 'X'
        and (
            STATUS_DPD is not null
            or IS_CLOSED is distinct from 0
            or IS_UNKNOWN is distinct from 1
        )
    )
    or (
        STATUS in ('0', '1', '2', '3', '4', '5')
        and (
            STATUS_DPD is distinct from try_cast(STATUS as integer)
            or IS_CLOSED is distinct from 0
            or IS_UNKNOWN is distinct from 0
        )
    )