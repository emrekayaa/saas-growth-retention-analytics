-- =====================================================================
-- 03) CHURN ROOT CAUSE: hangi kanaldan gelen musteriler daha cok churn ediyor?
-- Amac: Genel churn oranindaki artisin/anomalinin KOK NEDENINI bulmak.
-- Ilan maddesi: "Enable visibility into historical data and provide the
-- ability to identify the root causes of change"
-- =====================================================================

SELECT
    u.acquisition_channel,
    COUNT(*)                                                     AS paid_customers,
    SUM(s.is_churned)                                            AS churned_customers,
    ROUND(100.0 * SUM(s.is_churned) / COUNT(*), 1)               AS churn_rate_pct,
    ROUND(AVG(s.mrr), 1)                                         AS avg_mrr,
    -- churn'un toplam kayip gelire etkisi (is etkisini gostermek icin)
    ROUND(SUM(CASE WHEN s.is_churned = 1 THEN s.mrr ELSE 0 END), 1) AS mrr_lost_estimate
FROM subscriptions s
JOIN users u ON u.user_id = s.user_id
WHERE s.plan != 'free'
GROUP BY u.acquisition_channel
ORDER BY churn_rate_pct DESC;

-- Yorum notu (notebook'ta detaylandirilacak):
-- Eger bir kanalin churn_rate_pct'i belirgin sekilde diger kanallardan
-- yuksekse, bu "genel churn arttı" seklinde raporlanacak bir metrigin
-- ASIL KOK NEDENININ o kanaldaki trafik kalitesi oldugunu gosterir.
-- Growth ekibine "genel churn %X arttı" demek yerine
-- "paid_social kanalindan gelen musterilerin churn'u digerlerinin 2 kati,
-- ve bu kanalin payi son ceyrekte artti" demek ACTIONABLE bir insight'tir.
