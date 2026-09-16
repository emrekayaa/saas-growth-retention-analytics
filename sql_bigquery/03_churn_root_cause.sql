-- BigQuery Standard SQL versiyonu
-- Fark: SUM(s.is_churned) calismaz (BOOLEAN toplanamaz) -> COUNTIF(s.is_churned)
-- Fark: CASE WHEN...ELSE 0 END yerine kisa yol: IF(kosul, deger1, deger2)

SELECT
    u.acquisition_channel,
    COUNT(*)                                          AS paid_customers,
    COUNTIF(s.is_churned)                             AS churned_customers,
    ROUND(100.0 * COUNTIF(s.is_churned) / COUNT(*), 1) AS churn_rate_pct,
    ROUND(AVG(s.mrr), 1)                              AS avg_mrr,
    ROUND(SUM(IF(s.is_churned, s.mrr, 0)), 1)         AS mrr_lost_estimate
FROM `jotform_analytics.subscriptions` s
JOIN `jotform_analytics.users` u ON u.user_id = s.user_id
WHERE s.plan != 'free'
GROUP BY u.acquisition_channel
ORDER BY churn_rate_pct DESC;
