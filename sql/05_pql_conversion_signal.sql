-- =====================================================================
-- 05) "HANGI KULLANICI PRO SATIN ALIR?" -- Product Qualified Lead sinyali
-- Amac: Orhan Can notundaki "Hangi kullanici Pro satin alir -> Segment
-- analizi" sorusunu SQL ile cevaplamak. Bu sorgunun ciktisi ayrica
-- 06_churn_prediction Python modelinin feature'larindan biri olacak.
-- =====================================================================

WITH first_week_activity AS (
    SELECT
        u.user_id,
        u.company_size,
        u.acquisition_channel,
        COUNT(f.form_id) AS forms_in_first_week
    FROM users u
    LEFT JOIN forms f
        ON f.user_id = u.user_id
        AND f.created_at <= date(u.signup_date, '+7 days')
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
    JOIN subscriptions s ON s.user_id = fw.user_id
)
SELECT
    activity_bucket,
    COUNT(*)                                                     AS total_users,
    SUM(CASE WHEN plan != 'free' THEN 1 ELSE 0 END)              AS converted_to_paid,
    ROUND(100.0 * SUM(CASE WHEN plan != 'free' THEN 1 ELSE 0 END) / COUNT(*), 1) AS conversion_rate_pct
FROM labeled
GROUP BY activity_bucket
ORDER BY conversion_rate_pct DESC;
