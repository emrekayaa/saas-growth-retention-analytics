-- BigQuery Standard SQL versiyonu
-- Fark: SQLite'in date(col, '+7 days') yerine BigQuery'nin DATE_ADD(DATE(col), INTERVAL 7 DAY)

WITH first_week_activity AS (
    SELECT
        u.user_id,
        u.company_size,
        u.acquisition_channel,
        COUNT(f.form_id) AS forms_in_first_week
    FROM `jotform_analytics.users` u
    LEFT JOIN `jotform_analytics.forms` f
        ON f.user_id = u.user_id
        AND DATE(f.created_at) <= DATE_ADD(DATE(u.signup_date), INTERVAL 7 DAY)
    GROUP BY u.user_id, u.company_size, u.acquisition_channel
),
labeled AS (
    SELECT
        fw.user_id,
        fw.company_size,
        fw.acquisition_channel,
        CASE WHEN fw.forms_in_first_week >= 3 THEN 'high_activity_week1'
             WHEN fw.forms_in_first_week BETWEEN 1 AND 2 THEN 'low_activity_week1'
             ELSE 'no_activity_week1' END AS activity_bucket,
        s.plan
    FROM first_week_activity fw
    JOIN `jotform_analytics.subscriptions` s ON s.user_id = fw.user_id
)
SELECT
    activity_bucket,
    COUNT(*)                                          AS total_users,
    COUNTIF(plan != 'free')                           AS converted_to_paid,
    ROUND(100.0 * COUNTIF(plan != 'free') / COUNT(*), 1) AS conversion_rate_pct
FROM labeled
GROUP BY activity_bucket
ORDER BY conversion_rate_pct DESC;
