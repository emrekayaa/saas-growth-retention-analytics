-- BigQuery Standard SQL versiyonu
-- Fark: SQLite'in strftime('%Y-%m', ...) yerine BigQuery'nin FORMAT_DATE() kullanilir.
-- signup_date DATETIME/TIMESTAMP oldugu icin once DATE()'e cast ediyoruz.

WITH paid_users AS (
    SELECT
        s.user_id,
        u.acquisition_channel,
        FORMAT_DATE('%Y-%m', DATE(u.signup_date)) AS signup_month,
        s.start_date,
        s.is_churned
    FROM `jotform_analytics.subscriptions` s
    JOIN `jotform_analytics.users` u ON u.user_id = s.user_id
    WHERE s.plan != 'free'
),
cohort_size AS (
    SELECT signup_month, COUNT(*) AS cohort_users
    FROM paid_users
    GROUP BY signup_month
)
SELECT
    p.signup_month,
    cs.cohort_users,
    COUNTIF(NOT p.is_churned)                                  AS still_active,
    ROUND(100.0 * COUNTIF(NOT p.is_churned) / cs.cohort_users, 1) AS retention_pct
FROM paid_users p
JOIN cohort_size cs ON cs.signup_month = p.signup_month
GROUP BY p.signup_month, cs.cohort_users
ORDER BY p.signup_month;
