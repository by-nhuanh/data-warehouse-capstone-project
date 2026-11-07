-- Tổng hợp theo kỳ để tránh cộng lặp AMT_INSTALMENT

WITH payment AS (
    SELECT
        SK_ID_CURR,
        SK_ID_PREV,
        NUM_INSTALMENT_VERSION,
        NUM_INSTALMENT_NUMBER,

        TRY_CAST(
            AMT_PAYMENT AS DECIMAL(20,4)
        ) AS paid,

        TRY_CAST(
            AMT_INSTALMENT AS DECIMAL(20,4)
        ) AS due,

        TRY_CAST(
            DAYS_INSTALMENT AS INTEGER
        ) AS DAYS_INSTALMENT,

        TRY_CAST(
            DAYS_ENTRY_PAYMENT AS INTEGER
        ) AS DAYS_ENTRY_PAYMENT

    FROM {{ ref('stg_installments_payments') }}
)

SELECT
    SK_ID_PREV,
    NUM_INSTALMENT_VERSION,
    NUM_INSTALMENT_NUMBER,

    MAX(SK_ID_CURR) AS SK_ID_CURR,

    COUNT(*) AS payment_events,

    COUNT(DISTINCT SK_ID_CURR) AS customer_count,

    COUNT(DISTINCT due) AS distinct_due_count,

    COUNT(*) FILTER (
        WHERE paid IS NULL
    ) AS null_payment_count,

    SUM(paid) AS total_paid,

    MAX(due) AS installment_due,

    -- Chênh lệch giữa ngày thanh toán cuối và ngày đến hạn
    CASE
        WHEN COUNT(*) FILTER (
            WHERE DAYS_INSTALMENT IS NULL
               OR DAYS_ENTRY_PAYMENT IS NULL
        ) > 0
        OR COUNT(DISTINCT DAYS_INSTALMENT) <> 1
        THEN NULL

        ELSE
            MAX(DAYS_ENTRY_PAYMENT)
            - MAX(DAYS_INSTALMENT)

    END AS days_late_last_payment,

    -- Cờ nhận diện có ít nhất một lần thanh toán trễ
    CASE
        WHEN COUNT(*) FILTER (
            WHERE DAYS_INSTALMENT IS NULL
               OR DAYS_ENTRY_PAYMENT IS NULL
        ) > 0
        OR COUNT(DISTINCT DAYS_INSTALMENT) <> 1
        THEN NULL

        WHEN MAX(
            CASE
                WHEN DAYS_ENTRY_PAYMENT > DAYS_INSTALMENT
                THEN 1
                ELSE 0
            END
        ) = 1
        THEN 1

        ELSE 0

    END AS has_late_payment

FROM payment

GROUP BY
    SK_ID_PREV,
    NUM_INSTALMENT_VERSION,
    NUM_INSTALMENT_NUMBER
