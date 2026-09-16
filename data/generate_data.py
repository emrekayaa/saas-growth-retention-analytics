"""
SaaS Growth & Retention Analytics — Synthetic Data Generator (v2 - BUYUK OLCEK)
(Cevrimici form-olusturucu bir SaaS platformunu temsil eden jenerik bir vaka calismasi)
====================================================================================
v1'e gore degisenler:
  - Kullanici sayisi 18.000 -> 120.000 (forms/submissions/events orantili buyudu,
    toplamda ~1.5 milyon satira yakin bir veri seti -> gercek bir BigQuery projesi
    hissi vermesi icin)
  - Her tabloya ek, gercekci sutunlar eklendi (browser, os, utm, billing_cycle, vb.)
  - 2 YENI TABLO: support_tickets, marketing_spend
    -> Bu ikisi, churn kok neden hikayesini bir kat daha derinlestiriyor:
       churn eden kullanicilarin churn'den once daha cok/daha kotu puanli
       destek talebi actigini, ve paid_social kanalinin ucuz ama dusuk kaliteli
       oldugunu (CAC dusuk, churn yuksek) SQL ile kesfedebileceksin.

Gomulu sinyaller (v1'den korunanlar + yeniler):
  1) paid_social kanali daha yuksek churn (ROOT CAUSE)
  2) smart_field_suggestions A/B testinde treatment daha yuksek publish rate
  3) formlarin kucuk bir yuzdesinde bot/spam submission patlamasi (FRAUD)
  4) ilk hafta >=3 form olusturanlarin Pro'ya gecme ihtimali daha yuksek (PQL)
  5) YENI: yillik (annual) billing_cycle secen kullanicilar aylik olanlara gore
     daha az churn ediyor (bilinen bir SaaS gercekligi)
  6) YENI: churn eden kullanicilar, churn'den once daha fazla ve daha dusuk
     csat'li support ticket aciyor
  7) YENI: paid_social'in CAC'i (musteri edinme maliyeti) dusuk ama churn'u
     yuksek oldugu icin gercek LTV:CAC orani digerlerinden kotu
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import hashlib
import os
from faker import Faker

np.random.seed(42)
fake = Faker()
Faker.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "raw")
DB_PATH = os.path.join(os.path.dirname(__file__), "saas_analytics.db")
os.makedirs(OUT_DIR, exist_ok=True)

N_USERS = 120_000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
AB_TEST_START = datetime(2024, 6, 1)
AB_TEST_END = datetime(2024, 7, 15)

CHANNELS = ["organic_search", "paid_search", "paid_social", "referral", "content_marketing"]
CHANNEL_WEIGHTS = [0.30, 0.22, 0.20, 0.13, 0.15]
UTM_SOURCE_MAP = {
    "organic_search": ["google", "bing", "duckduckgo"],
    "paid_search": ["google_ads", "bing_ads"],
    "paid_social": ["facebook_ads", "instagram_ads", "tiktok_ads"],
    "referral": ["partner_site", "affiliate"],
    "content_marketing": ["blog", "youtube", "newsletter"],
}
COMPANY_SIZES = ["solo", "small_team", "smb", "enterprise"]
COMPANY_WEIGHTS = [0.45, 0.30, 0.18, 0.07]
COUNTRIES = ["US", "TR", "UK", "DE", "CA", "AU", "IN", "BR", "FR", "NL"]
COUNTRY_WEIGHTS = [0.35, 0.08, 0.10, 0.08, 0.07, 0.05, 0.09, 0.06, 0.06, 0.06]
CATEGORIES = ["contact_form", "survey", "registration", "payment_form", "order_form", "feedback", "job_application", "other"]
DEVICE_TYPES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Other"]
BROWSER_WEIGHTS = [0.55, 0.20, 0.10, 0.10, 0.05]
OS_LIST = ["Windows", "macOS", "iOS", "Android", "Linux"]
OS_WEIGHTS = [0.42, 0.22, 0.15, 0.16, 0.05]
LANGUAGES = ["en", "tr", "es", "de", "fr", "pt"]
LANGUAGE_WEIGHTS = [0.45, 0.10, 0.15, 0.10, 0.10, 0.10]
PERSONAL_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]

def random_dates(n, start, end):
    delta_days = (end - start).days
    offsets = np.random.randint(0, delta_days, size=n)
    return [start + timedelta(days=int(o)) for o in offsets]

# ---------------------------------------------------------------
# 1) USERS
# ---------------------------------------------------------------
user_ids = np.arange(1, N_USERS + 1)
signup_dates = random_dates(N_USERS, START_DATE, END_DATE)
channels = np.random.choice(CHANNELS, N_USERS, p=CHANNEL_WEIGHTS)
company_sizes = np.random.choice(COMPANY_SIZES, N_USERS, p=COMPANY_WEIGHTS)
countries = np.random.choice(COUNTRIES, N_USERS, p=COUNTRY_WEIGHTS)
browsers = np.random.choice(BROWSERS, N_USERS, p=BROWSER_WEIGHTS)
oses = np.random.choice(OS_LIST, N_USERS, p=OS_WEIGHTS)
is_email_verified = np.random.rand(N_USERS) < 0.88

utm_sources = np.array([np.random.choice(UTM_SOURCE_MAP[c]) for c in channels])

# email_domain: enterprise/smb kurumsal domain kullanma egiliminde, solo/small_team kisisel domain
email_domains = []
for cs in company_sizes:
    if cs in ("smb", "enterprise") and np.random.rand() < 0.7:
        email_domains.append(fake.free_email_domain() if np.random.rand() < 0.0 else fake.domain_name())
    else:
        email_domains.append(np.random.choice(PERSONAL_EMAIL_DOMAINS))

users = pd.DataFrame({
    "user_id": user_ids,
    "signup_date": signup_dates,
    "acquisition_channel": channels,
    "utm_source": utm_sources,
    "company_size": company_sizes,
    "country": countries,
    "browser": browsers,
    "operating_system": oses,
    "email_domain": email_domains,
    "is_email_verified": is_email_verified,
})
users = users.sort_values("signup_date").reset_index(drop=True)

print(f"[1/8] users olusturuldu: {len(users):,}")

# ---------------------------------------------------------------
# 2) A/B TEST ASSIGNMENT
# ---------------------------------------------------------------
in_window = (users["signup_date"] >= AB_TEST_START) & (users["signup_date"] <= AB_TEST_END)
ab_users = users.loc[in_window, "user_id"].values
variant_assignment = np.random.choice(["control", "treatment"], size=len(ab_users), p=[0.5, 0.5])
ab_test = pd.DataFrame({
    "user_id": ab_users,
    "variant": variant_assignment,
    "assigned_at": users.loc[in_window, "signup_date"].values,
})
variant_map = dict(zip(ab_test.user_id, ab_test.variant))
print(f"[2/8] ab_test_assignments olusturuldu: {len(ab_test):,}")

# ---------------------------------------------------------------
# 3) FORMS
# ---------------------------------------------------------------
form_rows = []
form_id_counter = 1
user_form_count = {}

FORM_NAME_PREFIX = {
    "contact_form": ["Contact Us", "Get in Touch", "Support Request Form", "General Inquiry"],
    "survey": ["Customer Satisfaction Survey", "NPS Survey", "Product Feedback Survey", "Market Research Survey"],
    "registration": ["Event Registration", "Webinar Signup", "Workshop Registration", "Membership Application"],
    "payment_form": ["Invoice Payment", "Donation Form", "Checkout Form", "Subscription Payment"],
    "order_form": ["Product Order Form", "Purchase Request", "Catering Order", "Custom Order Form"],
    "feedback": ["Feedback Form", "Service Rating", "Post-Visit Feedback", "Employee Feedback"],
    "job_application": ["Job Application", "Internship Application", "Career Portal Form", "Resume Submission"],
    "other": ["Untitled Form", "New Form", "Draft Form", "Custom Form"],
}

for _, u in users.iterrows():
    base_lambda = {"solo": 1.3, "small_team": 2.2, "smb": 3.0, "enterprise": 4.2}[u.company_size]
    variant = variant_map.get(u.user_id)
    if variant == "treatment":
        base_lambda *= 1.25

    n_forms = max(np.random.poisson(base_lambda), 0)
    first_week_count = 0

    for i in range(n_forms):
        days_range = (END_DATE - u.signup_date).days
        if days_range <= 0:
            continue
        days_after = min(int(np.random.exponential(40)), days_range)
        created_at = u.signup_date + timedelta(days=days_after)
        if created_at > END_DATE:
            continue
        if days_after <= 7:
            first_week_count += 1

        category = np.random.choice(CATEGORIES, p=[0.28, 0.18, 0.12, 0.10, 0.10, 0.12, 0.05, 0.05])
        field_count = max(1, int(np.random.normal(7, 3)))
        language = np.random.choice(LANGUAGES, p=LANGUAGE_WEIGHTS)
        has_payment_field = (category == "payment_form") or (np.random.rand() < 0.05)
        integration_count = np.random.poisson(0.8)

        base_publish_p = 0.74 if variant == "treatment" else 0.62
        is_published = np.random.rand() < base_publish_p

        form_rows.append({
            "form_id": form_id_counter,
            "user_id": u.user_id,
            "created_at": created_at,
            "category": category,
            "form_name": f"{np.random.choice(FORM_NAME_PREFIX[category])} #{form_id_counter}",
            "field_count": field_count,
            "language": language,
            "has_payment_field": bool(has_payment_field),
            "integration_count": int(integration_count),
            "is_published": is_published,
        })
        form_id_counter += 1

    user_form_count[u.user_id] = first_week_count

forms = pd.DataFrame(form_rows)
print(f"[3/8] forms olusturuldu: {len(forms):,}")

# ---------------------------------------------------------------
# 4) SUBSCRIPTIONS
# ---------------------------------------------------------------
sub_rows = []
PLAN_MRR = {"free": 0, "bronze": 15, "silver": 29, "gold": 49}
PAYMENT_METHODS = ["credit_card", "paypal", "bank_transfer"]

for _, u in users.iterrows():
    fw_forms = user_form_count.get(u.user_id, 0)
    size_boost = {"solo": 0.0, "small_team": 0.03, "smb": 0.08, "enterprise": 0.15}[u.company_size]
    pql_boost = 0.18 if fw_forms >= 3 else 0.0
    channel_penalty = -0.05 if u.acquisition_channel == "paid_social" else 0.0

    convert_p = np.clip(0.12 + size_boost + pql_boost + channel_penalty, 0.02, 0.85)
    converted = np.random.rand() < convert_p

    billing_cycle = np.random.choice(["monthly", "annual"], p=[0.7, 0.3]) if converted else "monthly"
    payment_method = np.random.choice(PAYMENT_METHODS, p=[0.75, 0.18, 0.07])

    if converted:
        plan = np.random.choice(["bronze", "silver", "gold"], p=[0.5, 0.35, 0.15])
        start_days_after = int(np.random.exponential(20))
        start_date = u.signup_date + timedelta(days=start_days_after)
        if start_date > END_DATE:
            plan = "free"
            start_date = u.signup_date
            billing_cycle = "monthly"
    else:
        plan = "free"
        start_date = u.signup_date

    # CHURN: paid_social + aylik faturalama churn'u artiriyor, yillik azaltiyor
    churned = False
    churn_date = None
    if plan != "free":
        base_churn_p = 0.22
        if u.acquisition_channel == "paid_social":
            base_churn_p = 0.42
        if billing_cycle == "annual":
            base_churn_p *= 0.45   # yillik plan sadakati artiriyor (gercek SaaS davranisi)
        churned = np.random.rand() < base_churn_p
        if churned:
            tenure_days = int(np.random.exponential(75))
            churn_date = start_date + timedelta(days=tenure_days)
            if churn_date > END_DATE:
                churned = False
                churn_date = None

    sub_rows.append({
        "user_id": u.user_id,
        "plan": plan,
        "mrr": PLAN_MRR[plan],
        "billing_cycle": billing_cycle,
        "payment_method": payment_method,
        "start_date": start_date,
        "is_churned": churned,
        "churn_date": churn_date,
    })

subscriptions = pd.DataFrame(sub_rows)
print(f"[4/8] subscriptions olusturuldu: {len(subscriptions):,}")

# ---------------------------------------------------------------
# 5) EVENTS
# ---------------------------------------------------------------
EVENT_TYPES = ["login", "create_form", "publish_form", "upgrade_click", "use_widget", "add_payment_field"]
PLATFORMS = ["web", "mobile_app", "api"]
event_rows = []
event_id = 1
for _, u in users.iterrows():
    n_logins = np.random.poisson(8)
    days_range = (END_DATE - u.signup_date).days
    if days_range <= 0:
        continue
    for _ in range(n_logins):
        days_after = np.random.randint(0, days_range)
        ev_date = u.signup_date + timedelta(days=int(days_after))
        if ev_date > END_DATE:
            continue
        event_rows.append({
            "event_id": event_id,
            "user_id": u.user_id,
            "event_type": np.random.choice(EVENT_TYPES, p=[0.55, 0.20, 0.10, 0.05, 0.06, 0.04]),
            "platform": np.random.choice(PLATFORMS, p=[0.75, 0.20, 0.05]),
            "event_date": ev_date,
        })
        event_id += 1

events = pd.DataFrame(event_rows)
print(f"[5/8] events olusturuldu: {len(events):,}")

# ---------------------------------------------------------------
# 6) SUBMISSIONS (fraud pattern gomulu)
# ---------------------------------------------------------------
sub_form_rows = []
submission_id = 1
published_forms = forms[forms.is_published].copy()
REFERRER_DOMAINS = ["google.com", "facebook.com", "instagram.com", "direct", "linkedin.com", "twitter.com"]

for _, f in published_forms.iterrows():
    n_subs = np.random.poisson(6)
    for _ in range(n_subs):
        days_after = np.random.randint(0, 60)
        submitted_at = f.created_at + timedelta(days=int(days_after))
        if submitted_at > END_DATE:
            continue
        completion_time = max(5, np.random.normal(90, 40))
        is_partial = np.random.rand() < 0.12
        sub_form_rows.append({
            "submission_id": submission_id,
            "form_id": f.form_id,
            "submitted_at": submitted_at,
            "device_type": np.random.choice(DEVICE_TYPES, p=[0.45, 0.48, 0.07]),
            "browser": np.random.choice(BROWSERS, p=BROWSER_WEIGHTS),
            "referrer_domain": np.random.choice(REFERRER_DOMAINS, p=[0.25, 0.15, 0.10, 0.30, 0.10, 0.10]),
            "completion_time_sec": round(completion_time, 1),
            "is_partial": bool(is_partial),
            "ip_hash": hashlib.md5(f"user_{f.user_id}_{np.random.randint(0,999)}".encode()).hexdigest()[:10],
        })
        submission_id += 1

fraud_forms = published_forms.sample(frac=0.004, random_state=1)
fake_ip = hashlib.md5(b"bot_farm_ip").hexdigest()[:10]
for _, f in fraud_forms.iterrows():
    burst_start = f.created_at + timedelta(days=int(np.random.randint(1, 30)))
    n_burst = np.random.randint(30, 70)
    for i in range(n_burst):
        submitted_at = burst_start + timedelta(seconds=int(np.random.randint(0, 600)))
        if submitted_at > END_DATE:
            continue
        sub_form_rows.append({
            "submission_id": submission_id,
            "form_id": f.form_id,
            "submitted_at": submitted_at,
            "device_type": "desktop",
            "browser": "Other",
            "referrer_domain": "direct",
            "completion_time_sec": round(np.random.uniform(1, 4), 1),
            "is_partial": False,
            "ip_hash": fake_ip,
        })
        submission_id += 1

submissions = pd.DataFrame(sub_form_rows)
print(f"[6/8] submissions olusturuldu: {len(submissions):,}")

# ---------------------------------------------------------------
# 7) SUPPORT TICKETS (YENI TABLO)
# Sinyal: churn eden kullanicilar churn'den once daha fazla / daha dusuk
# puanli destek talebi aciyor.
# ---------------------------------------------------------------
TICKET_CATEGORIES = ["billing", "technical", "feature_request", "bug_report", "account_access", "other"]
PRIORITIES = ["low", "medium", "high"]
ticket_rows = []
ticket_id = 1

sub_lookup = subscriptions.set_index("user_id")

for _, u in users.iterrows():
    sub = sub_lookup.loc[u.user_id]
    will_churn = bool(sub["is_churned"])
    # churn edecek kullanicilar ortalama daha fazla ticket aciyor (2.2x)
    base_tickets = np.random.poisson(0.6)
    extra_tickets = np.random.poisson(1.0) if will_churn else 0
    n_tickets = base_tickets + extra_tickets
    if n_tickets == 0:
        continue

    days_range = (END_DATE - u.signup_date).days
    if days_range <= 0:
        continue

    for _ in range(n_tickets):
        days_after = np.random.randint(0, days_range)
        created_at = u.signup_date + timedelta(days=int(days_after))
        if created_at > END_DATE:
            continue
        category = np.random.choice(TICKET_CATEGORIES, p=[0.22, 0.28, 0.18, 0.15, 0.10, 0.07])
        priority = np.random.choice(PRIORITIES, p=[0.5, 0.35, 0.15])
        resolved = np.random.rand() < (0.70 if not will_churn else 0.50)
        resolution_time_hours = round(np.random.exponential(18), 1) if resolved else None
        # churn edecek kullanicilar sisteme daha dusuk csat veriyor
        if resolved:
            csat = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.10, 0.15, 0.30, 0.40]) if not will_churn \
                   else np.random.choice([1, 2, 3, 4, 5], p=[0.20, 0.25, 0.25, 0.20, 0.10])
        else:
            csat = None

        ticket_rows.append({
            "ticket_id": ticket_id,
            "user_id": u.user_id,
            "created_at": created_at,
            "category": category,
            "priority": priority,
            "is_resolved": bool(resolved),
            "resolution_time_hours": resolution_time_hours,
            "csat_score": csat,
        })
        ticket_id += 1

support_tickets = pd.DataFrame(ticket_rows)
print(f"[7/8] support_tickets olusturuldu: {len(support_tickets):,}")

# ---------------------------------------------------------------
# 8) MARKETING SPEND (YENI TABLO)
# Kanal x ay bazinda harcama -> CAC hesaplanabilir hale geliyor.
# Sinyal: paid_social'in CAC'i dusuk (ucuz trafik) ama churn'u yuksek
# -> LTV:CAC orani aslinda kotu (root-cause hikayesine is boyutu katiyor)
# ---------------------------------------------------------------
CHANNEL_MONTHLY_BUDGET = {
    "paid_search": (18000, 28000),
    "paid_social": (10000, 16000),
    "content_marketing": (4000, 7000),
}
months = pd.date_range(START_DATE, END_DATE, freq="MS").strftime("%Y-%m").tolist()
signup_month_counts = users.copy()
signup_month_counts["signup_month"] = pd.to_datetime(signup_month_counts["signup_date"]).dt.strftime("%Y-%m")
monthly_channel_signups = signup_month_counts.groupby(["signup_month", "acquisition_channel"]).size()

spend_rows = []
for month in months:
    for channel, (low, high) in CHANNEL_MONTHLY_BUDGET.items():
        spend = round(np.random.uniform(low, high), 2)
        impressions = int(spend * np.random.uniform(40, 60))
        clicks = int(impressions * np.random.uniform(0.015, 0.035))
        attributed_signups = int(monthly_channel_signups.get((month, channel), 0))
        spend_rows.append({
            "channel": channel,
            "month": month,
            "spend_usd": spend,
            "impressions": impressions,
            "clicks": clicks,
            "attributed_signups": attributed_signups,
        })
    # organik/referral kanallar icin harcama yok ama takip icin 0 satir ekliyoruz
    for channel in ["organic_search", "referral"]:
        attributed_signups = int(monthly_channel_signups.get((month, channel), 0))
        spend_rows.append({
            "channel": channel,
            "month": month,
            "spend_usd": 0.0,
            "impressions": 0,
            "clicks": 0,
            "attributed_signups": attributed_signups,
        })

marketing_spend = pd.DataFrame(spend_rows)
print(f"[8/8] marketing_spend olusturuldu: {len(marketing_spend):,}")

# ---------------------------------------------------------------
# TARIH SUTUNLARINI TUTARLI HALE GETIR
# ---------------------------------------------------------------
DATE_FMT = "%Y-%m-%d %H:%M:%S"
users["signup_date"] = pd.to_datetime(users["signup_date"])
forms["created_at"] = pd.to_datetime(forms["created_at"])
subscriptions["start_date"] = pd.to_datetime(subscriptions["start_date"])
subscriptions["churn_date"] = pd.to_datetime(subscriptions["churn_date"])
events["event_date"] = pd.to_datetime(events["event_date"])
submissions["submitted_at"] = pd.to_datetime(submissions["submitted_at"])
support_tickets["created_at"] = pd.to_datetime(support_tickets["created_at"])
ab_test["assigned_at"] = pd.to_datetime(ab_test["assigned_at"])

# ---------------------------------------------------------------
# KAYDET
# ---------------------------------------------------------------
users.to_csv(f"{OUT_DIR}/users.csv", index=False, date_format=DATE_FMT)
forms.to_csv(f"{OUT_DIR}/forms.csv", index=False, date_format=DATE_FMT)
subscriptions.to_csv(f"{OUT_DIR}/subscriptions.csv", index=False, date_format=DATE_FMT)
events.to_csv(f"{OUT_DIR}/events.csv", index=False, date_format=DATE_FMT)
submissions.to_csv(f"{OUT_DIR}/submissions.csv", index=False, date_format=DATE_FMT)
ab_test.to_csv(f"{OUT_DIR}/ab_test_assignments.csv", index=False, date_format=DATE_FMT)
support_tickets.to_csv(f"{OUT_DIR}/support_tickets.csv", index=False, date_format=DATE_FMT)
marketing_spend.to_csv(f"{OUT_DIR}/marketing_spend.csv", index=False)

conn = sqlite3.connect(DB_PATH)
users.to_sql("users", conn, if_exists="replace", index=False)
forms.to_sql("forms", conn, if_exists="replace", index=False)
subscriptions.to_sql("subscriptions", conn, if_exists="replace", index=False)
events.to_sql("events", conn, if_exists="replace", index=False)
submissions.to_sql("submissions", conn, if_exists="replace", index=False)
ab_test.to_sql("ab_test_assignments", conn, if_exists="replace", index=False)
support_tickets.to_sql("support_tickets", conn, if_exists="replace", index=False)
marketing_spend.to_sql("marketing_spend", conn, if_exists="replace", index=False)
conn.close()

print("\nUretim tamamlandi. Toplam satir sayisi:",
      f"{len(users)+len(forms)+len(subscriptions)+len(events)+len(submissions)+len(ab_test)+len(support_tickets)+len(marketing_spend):,}")
