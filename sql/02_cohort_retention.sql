-- =====================================================================
-- 02) MONTHLY COHORT RETENTION (paid users)
-- Amac: Kullanicilari kayit ayina gore cohortlara ayirip, her cohort'un
-- kac ay sonra hala aktif (churn etmemis) oldugunu olcmek.
-- =====================================================================

WITH paid_users AS (
    SELECT
        s.user_id,
        u.acquisition_channel,
        strftime('%Y-%m', u.signup_date) AS signup_month,
        s.start_date,
        s.is_churned,
        s.churn_date
    FROM subscriptions s
    JOIN users u ON u.user_id = s.user_id
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
    SUM(CASE WHEN p.is_churned = 0 THEN 1 ELSE 0 END) AS still_active,
    ROUND(100.0 * SUM(CASE WHEN p.is_churned = 0 THEN 1 ELSE 0 END) / cs.cohort_users, 1) AS retention_pct
FROM paid_users p
JOIN cohort_size cs ON cs.signup_month = p.signup_month
GROUP BY p.signup_month, cs.cohort_users
ORDER BY p.signup_month;

-- Kanal kirilimiyla retention (root cause analizine giris niteliginde)
-- Bu sorgu 03_churn_root_cause.sql'de detaylandiriliyor.
