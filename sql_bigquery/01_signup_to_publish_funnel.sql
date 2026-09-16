-- BigQuery Standard SQL versiyonu
-- Fark 1: Tablo adlari `dataset.table` formatinda (backtick ile)
-- Fark 2: is_published artik gercek BOOLEAN turunde -> MAX(CASE WHEN..=1) yerine LOGICAL_OR
-- Fark 3: COUNT(*) FILTER yerine BigQuery'nin COUNTIF() fonksiyonu kullanildi

WITH user_first_form AS (
    SELECT
        u.user_id,
        u.signup_date,
        u.acquisition_channel,
        u.company_size,
        MIN(f.created_at) AS first_form_date,
        COUNT(f.form_id)   AS total_forms_created
    FROM `jotform_analytics.users` u
    LEFT JOIN `jotform_analytics.forms` f ON f.user_id = u.user_id
    GROUP BY u.user_id, u.signup_date, u.acquisition_channel, u.company_size
),
user_publish AS (
    SELECT
        u.user_id,
        LOGICAL_OR(COALESCE(f.is_published, FALSE)) AS has_published_form
    FROM `jotform_analytics.users` u
    LEFT JOIN `jotform_analytics.forms` f ON f.user_id = u.user_id
    GROUP BY u.user_id
)
SELECT
    uf.acquisition_channel,
    COUNT(*)                                          AS total_signups,
    COUNTIF(uf.total_forms_created > 0)               AS created_a_form,
    COUNTIF(up.has_published_form)                    AS published_a_form,
    ROUND(100.0 * COUNTIF(uf.total_forms_created > 0) / COUNT(*), 1) AS pct_created_form,
    ROUND(100.0 * COUNTIF(up.has_published_form) / COUNT(*), 1)      AS pct_published_form
FROM user_first_form uf
JOIN user_publish up ON up.user_id = uf.user_id
GROUP BY uf.acquisition_channel
ORDER BY pct_published_form DESC;
