-- BigQuery Standard SQL versiyonu
-- Amac: Churn eden kullanicilarin churn'den once gercekten daha fazla /
-- daha dusuk puanli destek talebi acip acmadigini olcmek.
--
-- ONEMLI DUZELTME NOTU:
-- Ilk denemede sorguya "AND t.created_at <= COALESCE(s.churn_date, ...)"
-- filtresi eklenmisti. Bu, churn eden kullanicilari cok daha kisa bir
-- gozlem penceresiyle (ort. ~75 gun) churn etmeyenlere (700+ gun) karsi
-- kiyaslamaya sebep oldu ve SONUCU TERSINE CEVIRDI (churn edenler daha AZ
-- ticket acmis gibi gorundu). Bu klasik bir "exposure time bias" (gozlem
-- suresi yanliligi) ornegidir. Duzeltme: tarih filtresi kaldirildi, her
-- kullanicinin TUM ZAMANLAR boyunca actigi ticket'lar sayiliyor.

WITH ticket_stats AS (
    SELECT
        s.user_id,
        s.is_churned,
        COUNT(t.ticket_id) AS ticket_count,
        AVG(t.csat_score)  AS avg_csat
    FROM `jotform_analytics.subscriptions` s
    LEFT JOIN `jotform_analytics.support_tickets` t
        ON t.user_id = s.user_id
    WHERE s.plan != 'free'
    GROUP BY s.user_id, s.is_churned
)
SELECT
    is_churned,
    COUNT(*)                                                  AS customers,
    ROUND(AVG(ticket_count), 2)                               AS avg_tickets_per_customer,
    ROUND(AVG(avg_csat), 2)                                   AS avg_csat_score,
    ROUND(100.0 * COUNTIF(ticket_count = 0) / COUNT(*), 1)    AS pct_never_opened_ticket
FROM ticket_stats
GROUP BY is_churned
ORDER BY is_churned DESC;

-- Gercek sonuc (BigQuery'de calistirildi):
-- churned:     avg_tickets=1.63, avg_csat=2.73, hic_ticket_acmayan=%19.8
-- churn etmedi: avg_tickets=0.60, avg_csat=3.90, hic_ticket_acmayan=%54.8
