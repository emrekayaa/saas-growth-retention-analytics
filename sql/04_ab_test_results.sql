-- =====================================================================
-- 04) A/B TEST: "smart_field_suggestions" ozelliginin form publish rate'ine etkisi
-- Amac: Ilandaki "Design A/B test, interpret and present the findings"
-- Istatistiksel anlamlilik testi (z-test / chi-square) Python notebook'ta yapilacak.
-- Bu sorgu ham sayilari (n, basari sayisi, oran) cikarir.
-- =====================================================================

WITH user_form_stats AS (
    SELECT
        ab.user_id,
        ab.variant,
        COUNT(f.form_id)                                       AS forms_created,
        SUM(CASE WHEN f.is_published = 1 THEN 1 ELSE 0 END)    AS forms_published,
        AVG(f.field_count)                                     AS avg_field_count
    FROM ab_test_assignments ab
    LEFT JOIN forms f ON f.user_id = ab.user_id
    GROUP BY ab.user_id, ab.variant
)
SELECT
    variant,
    COUNT(*)                                              AS n_users,
    SUM(forms_created)                                    AS total_forms_created,
    SUM(forms_published)                                  AS total_forms_published,
    ROUND(100.0 * SUM(forms_published) / NULLIF(SUM(forms_created), 0), 2) AS publish_rate_pct,
    ROUND(AVG(forms_created), 2)                          AS avg_forms_per_user,
    SUM(CASE WHEN forms_published > 0 THEN 1 ELSE 0 END) AS users_who_published_at_least_one
FROM user_form_stats
GROUP BY variant;
