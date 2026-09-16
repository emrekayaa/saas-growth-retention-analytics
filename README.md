# SaaS Growth & Retention Analytics — Case Study

Bu proje, **online form/anket oluşturma hizmeti veren bir SaaS şirketi** (JotForm, Typeform,
Google Forms gibi ürünleri düşünebilirsin) senaryosu üzerinden kurulmuş uçtan uca bir
Data Analyst vaka çalışmasıdır: SQL analizi, A/B test tasarımı ve istatistiksel doğrulama,
kök neden (root cause) analizi, davranışsal segmentasyon ve veri kalitesi kontrolü.

> **Not:** Gerçek bir şirketin verisi kullanılmadı. `data/generate_data.py`, bu tür bir SaaS
> ürününün gerçekçi iş dinamiklerini (kanal kalitesi farkı, özellik etkisi, bot trafiği,
> destek talebi—churn ilişkisi) bilinçli olarak içine gömen sentetik bir veri üretici
> scripttir. Amaç, gerçek bir veri ambarına (data warehouse) uygulanabilecek analiz
> metodolojisini uçtan uca göstermektir.

## Bir Senior Data Analyst rolünde beklenen yetkinlikler → Bu projede nerede

| Yetkinlik | Karşılığı |
|---|---|
| Strong SQL | `sql/` (SQLite) ve `sql_bigquery/` (BigQuery) klasörlerindeki 8 sorgu |
| Root cause identification | `sql/03_churn_root_cause.sql` + notebook bölüm 3 |
| A/B test design & interpretation | `sql/04_ab_test_results.sql` + notebook bölüm 4 (z-test, %95 GA) |
| Statistical measures (CI, significance) | Notebook boyunca `statsmodels.proportions_ztest` |
| Forecasts / predictive recommendations | `sql/05_pql_conversion_signal.sql` (segment sinyali) |
| Discover hidden patterns | `sql/06_fraud_pattern_detection.sql` (bot/spam tespiti) |
| Cross-functional business impact | `sql/07_support_ticket_churn_signal.sql`, `sql/08_channel_cac_vs_churn.sql` |
| Data visualization | Notebook'taki tüm grafikler (`matplotlib`) |
| BI / dashboard | Power BI dashboard (bkz. `dashboard/`) |

## Kurulum

```bash
pip install -r requirements.txt
python data/generate_data.py          # sentetik veriyi uretir -> data/saas_analytics.db
jupyter notebook notebooks/01_growth_analytics_case_study.ipynb
```

BigQuery üzerinde çalışmak istersen `sql_bigquery/` klasöründeki dosyaları kullan
(CSV'leri kendi BigQuery dataset'ine yükleyip tablo isimlerini birebir eşleştirmen yeterli).

## Proje yapısı

```
saas-growth-retention-analytics/
├── data/
│   ├── generate_data.py        # sentetik veri ureticisi (embedded sinyaller aciklamali)
│   ├── saas_analytics.db        # SQLite veritabani
│   └── raw/                     # CSV export'lar (8 tablo, ~2.4M satir)
├── sql/                          # SQLite versiyonu (8 sorgu)
├── sql_bigquery/                 # BigQuery Standard SQL versiyonu (8 sorgu)
├── notebooks/
│   └── 01_growth_analytics_case_study.ipynb
├── dashboard/                    # Power BI dosyaları
└── requirements.txt
```

## Veri seti ölçeği

| Tablo | Satır sayısı | Açıklama |
|---|---|---|
| `users` | 120,000 | Kullanıcı demografisi, kanal, cihaz bilgisi |
| `forms` | ~250,600 | Oluşturulan formlar, yayın durumu |
| `subscriptions` | 120,000 | Plan, faturalama döngüsü, churn durumu |
| `events` | ~960,000 | Uygulama içi davranış logu |
| `submissions` | ~882,600 | Formlara gelen yanıtlar |
| `support_tickets` | ~75,200 | Destek talepleri (churn ile ilişkili sinyal) |
| `marketing_spend` | 120 | Kanal x ay bazında pazarlama harcaması (CAC hesaplaması için) |
| `ab_test_assignments` | ~7,400 | A/B test grubu ataması |

**Toplam: ~2.4 milyon satır.**

## Öne çıkan bulgular

1. **Funnel:** Kanallar arası form oluşturma/yayınlama oranlarında anlamlı fark yok (~%83 / ~%69
   hepsinde) — yani sorun aktivasyonda değil.
2. **Churn kök nedeni:** `paid_social` kanalından gelen ücretli müşterilerin churn oranı
   (%31.5) diğer kanalların (~%16-18) yaklaşık 2 katı — istatistiksel olarak anlamlı.
3. **A/B test:** Yeni bir "akıllı alan önerisi" özelliği form yayınlama oranını %61.8'den
   %74.2'ye çıkarıyor (+12.3 puan) — istatistiksel olarak anlamlı, genel kullanıma açılması önerildi.
4. **PQL sinyali:** İlk hafta 3+ form oluşturan kullanıcılar, hiç form oluşturmayanlara göre
   ~2.2x daha yüksek oranda ücretli plana geçiyor.
5. **Destek talebi—churn ilişkisi:** Churn eden kullanıcılar, etmeyenlere göre ortalama 2.7x
   daha fazla destek talebi açıyor ve belirgin şekilde daha düşük memnuniyet puanı veriyor.
6. **CAC vs churn:** `paid_social` kanalı en ucuz müşteri edinme maliyetine sahip ama en yüksek
   churn'e de sahip — ham CAC'e bakarak bütçe kararı almanın yanıltıcı olabileceğini gösteriyor.
7. **Veri kalitesi:** Submission'ların ~%3-4'ü bot/spam pattern'i taşıyor; bu formlar
   raporlama öncesi filtrelenmeli.

## Sonraki adımlar

- [x] SQL analizi (8 sorgu, hem SQLite hem BigQuery)
- [x] İstatistiksel A/B test ve root cause doğrulaması (Python)
- [ ] Power BI dashboard
- [ ] Basit bir churn/conversion tahmin modeli
