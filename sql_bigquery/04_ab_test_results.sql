-- BigQuery Standard SQL versiyonu
-- Fark: COUNTIF(f.is_published) -> SUM(CASE WHEN...) yerine

WITH user_form_stats AS (
    SELECT
        ab.user_id,
        ab.variant,
        COUNT(f.form_id)             AS forms_created,
        COUNTIF(f.is_published)      AS forms_published,
        AVG(f.field_count)           AS avg_field_count
    FROM `jotform_analytics.ab_test_assignments` ab
    LEFT JOIN `jotform_analytics.forms` f ON f.user_id = ab.user_id
    GROUP BY ab.user_id, ab.variant
)
SELECT
    variant,
    COUNT(*)                                              AS n_users,
    SUM(forms_created)                                    AS total_forms_created,
    SUM(forms_published)                                  AS total_forms_published,
    ROUND(100.0 * SUM(forms_published) / NULLIF(SUM(forms_created), 0), 2) AS publish_rate_pct,
    ROUND(AVG(forms_created), 2)                          AS avg_forms_per_user,
    COUNTIF(forms_published > 0)                          AS users_who_published_at_least_one
FROM user_form_stats
GROUP BY variant;
