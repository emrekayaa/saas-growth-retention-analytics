-- BigQuery Standard SQL versiyonu
-- Amac: Her kanaldan bir musteri kazanmanin maliyetini (CAC), o kanalin
-- churn oraniyla birlikte degerlendirip "ucuz ama dusuk kaliteli trafik"
-- hikayesini kanitlamak.

WITH channel_totals AS (
    SELECT
        channel,
        SUM(spend_usd)          AS total_spend,
        SUM(attributed_signups) AS total_signups
    FROM `jotform_analytics.marketing_spend`
    GROUP BY channel
),
churn_by_channel AS (
    SELECT
        u.acquisition_channel AS channel,
        COUNT(*)                                          AS paid_customers,
        COUNTIF(s.is_churned)                             AS churned_customers,
        ROUND(100.0 * COUNTIF(s.is_churned) / COUNT(*), 1) AS churn_rate_pct,
        ROUND(AVG(s.mrr), 1)                              AS avg_mrr
    FROM `jotform_analytics.subscriptions` s
    JOIN `jotform_analytics.users` u ON u.user_id = s.user_id
    WHERE s.plan != 'free'
    GROUP BY u.acquisition_channel
)
SELECT
    c.channel,
    c.total_spend,
    c.total_signups,
    ROUND(SAFE_DIVIDE(c.total_spend, c.total_signups), 2) AS cac_usd,
    cb.churn_rate_pct,
    cb.avg_mrr
FROM channel_totals c
LEFT JOIN churn_by_channel cb ON cb.channel = c.channel
ORDER BY cac_usd DESC;
