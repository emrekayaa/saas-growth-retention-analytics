-- SQLite versiyonu (BigQuery karsiligi: sql_bigquery/07_support_ticket_churn_signal.sql)
-- Duzeltme notu icin BigQuery versiyonundaki aciklamaya bakiniz.

WITH ticket_stats AS (
    SELECT
        s.user_id,
        s.is_churned,
        COUNT(t.ticket_id) AS ticket_count,
        AVG(t.csat_score)  AS avg_csat
    FROM subscriptions s
    LEFT JOIN support_tickets t ON t.user_id = s.user_id
    WHERE s.plan != 'free'
    GROUP BY s.user_id, s.is_churned
)
SELECT
    is_churned,
    COUNT(*)                                                  AS customers,
    ROUND(AVG(ticket_count), 2)                               AS avg_tickets_per_customer,
    ROUND(AVG(avg_csat), 2)                                   AS avg_csat_score,
    ROUND(100.0 * SUM(CASE WHEN ticket_count = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_never_opened_ticket
FROM ticket_stats
GROUP BY is_churned
ORDER BY is_churned DESC;
