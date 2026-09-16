-- =====================================================================
-- 01) SIGNUP -> FIRST FORM -> PUBLISH FUNNEL
-- Amac: "Kullanici neden urunu birakiyor?" (funnel analizi)
-- Her kullanicinin: kayit oldu mu -> ilk formu olusturdu mu -> yayinladi mi
-- =====================================================================

WITH user_first_form AS (
    SELECT
        u.user_id,
        u.signup_date,
        u.acquisition_channel,
        u.company_size,
        MIN(f.created_at) AS first_form_date,
        COUNT(f.form_id)   AS total_forms_created
    FROM users u
    LEFT JOIN forms f ON f.user_id = u.user_id
    GROUP BY u.user_id, u.signup_date, u.acquisition_channel, u.company_size
),
user_publish AS (
    SELECT
        u.user_id,
        MAX(CASE WHEN f.is_published = 1 THEN 1 ELSE 0 END) AS has_published_form
    FROM users u
    LEFT JOIN forms f ON f.user_id = u.user_id
    GROUP BY u.user_id
)
SELECT
    uf.acquisition_channel,
    COUNT(*)                                              AS total_signups,
    SUM(CASE WHEN uf.total_forms_created > 0 THEN 1 ELSE 0 END)      AS created_a_form,
    SUM(up.has_published_form)                            AS published_a_form,
    ROUND(100.0 * SUM(CASE WHEN uf.total_forms_created > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_created_form,
    ROUND(100.0 * SUM(up.has_published_form) / COUNT(*), 1)                                   AS pct_published_form
FROM user_first_form uf
JOIN user_publish up ON up.user_id = uf.user_id
GROUP BY uf.acquisition_channel
ORDER BY pct_published_form DESC;
