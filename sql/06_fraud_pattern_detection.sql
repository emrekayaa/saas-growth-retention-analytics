-- =====================================================================
-- 06) SPAM / FRAUD SUBMISSION PATTERN DETECTION
-- Amac: Orhan Can notundaki "Spam/fraud submission var mi? -> Pattern
-- analizi" sorusunu SQL ile cevaplamak. Insan icin imkansiz derecede
-- hizli tamamlanan VE ayni IP'den kisa surede gelen submission
-- kumelerini yakaliyoruz.
-- =====================================================================

WITH ip_form_stats AS (
    SELECT
        form_id,
        ip_hash,
        COUNT(*)                           AS submissions_from_ip,
        AVG(completion_time_sec)           AS avg_completion_time,
        MIN(submitted_at)                  AS first_submit,
        MAX(submitted_at)                  AS last_submit
    FROM submissions
    GROUP BY form_id, ip_hash
)
SELECT
    form_id,
    ip_hash,
    submissions_from_ip,
    ROUND(avg_completion_time, 1) AS avg_completion_time_sec,
    first_submit,
    last_submit,
    -- flag: ayni IP'den 20'den fazla submission VE ortalama tamamlanma suresi 5 saniyeden az
    CASE
        WHEN submissions_from_ip > 20 AND avg_completion_time < 5 THEN 1
        ELSE 0
    END AS is_suspected_fraud
FROM ip_form_stats
WHERE submissions_from_ip > 20 AND avg_completion_time < 5
ORDER BY submissions_from_ip DESC;

-- Bu sorgu ile isaretlenen formlar, gercek bir urunde otomatik olarak
-- "review" kuyruguna alinabilir veya submission'lari raporlardan
-- filtrelenebilir (yanlis analiz/metrik sisirmesini onlemek icin).
