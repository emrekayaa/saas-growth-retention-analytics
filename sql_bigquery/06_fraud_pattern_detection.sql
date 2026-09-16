-- BigQuery Standard SQL versiyonu
-- Fark: sadece tablo referansi degisti, geri kalani ayni (tarih araligi
-- kullanilmadigi icin baska sozdizimi degisikligi gerekmiyor)

WITH ip_form_stats AS (
    SELECT
        form_id,
        ip_hash,
        COUNT(*)                    AS submissions_from_ip,
        AVG(completion_time_sec)    AS avg_completion_time,
        MIN(submitted_at)           AS first_submit,
        MAX(submitted_at)           AS last_submit
    FROM `jotform_analytics.submissions`
    GROUP BY form_id, ip_hash
)
SELECT
    form_id,
    ip_hash,
    submissions_from_ip,
    ROUND(avg_completion_time, 1) AS avg_completion_time_sec,
    first_submit,
    last_submit,
    IF(submissions_from_ip > 20 AND avg_completion_time < 5, 1, 0) AS is_suspected_fraud
FROM ip_form_stats
WHERE submissions_from_ip > 20 AND avg_completion_time < 5
ORDER BY submissions_from_ip DESC;
