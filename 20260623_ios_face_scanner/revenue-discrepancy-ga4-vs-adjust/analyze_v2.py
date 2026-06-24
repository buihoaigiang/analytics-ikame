"""
v2: Query đúng 3 event có revenue theo GA4 Events console:
  - app_store_subscription_renew  (80% revenue)
  - in_app_purchase               (16%)
  - app_store_subscription_convert (4%)
Date range mở rộng: May 27 - Jun 23 (28 ngày khớp với ảnh)
"""
import pandas as pd
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

CRED_PATH = r"C:\Users\admin\Desktop\analytics-ikame\20260623_ios_face_scanner\scan-vs-purchase-analysis\gcloud_credentials.json"
PROJECT   = "team-begamob"
DATE_FROM = "20260527"
DATE_TO   = "20260623"

creds  = Credentials.from_authorized_user_file(CRED_PATH)
client = bigquery.Client(credentials=creds, project=PROJECT)

pd.set_option("display.max_rows", 300)
pd.set_option("display.width", 200)

REVENUE_EVENTS = ("'app_store_subscription_renew',"
                  "'in_app_purchase',"
                  "'app_store_subscription_convert'")

# ── 1. Summary theo ngày + event ────────────────────────────────────────────
print("=" * 70)
print("1. REVENUE THEO NGÀY (3 events có revenue)")
print("=" * 70)

q1 = f"""
SELECT
  event_date,
  event_name,
  COUNT(*)                                                       AS event_count,
  STRING_AGG(DISTINCT
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'currency')
  )                                                              AS currencies,
  ROUND(SUM(
    COALESCE(
      (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value'),
      (SELECT value.float_value  FROM UNNEST(event_params) WHERE key = 'value'),
      0
    )
  ), 2)                                                          AS sum_value_raw
FROM `ios-face-scanner.analytics_540983063.events_intraday_*`
WHERE event_name IN ({REVENUE_EVENTS})
  AND _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
GROUP BY event_date, event_name
ORDER BY event_date, event_name
"""

df1 = client.query(q1).to_dataframe()
if df1.empty:
    print("Không có data trong intraday tables cho khoảng này.")
    print("→ Thử check xem có finalized tables không...")
else:
    print(df1.to_string(index=False))
    print(f"\nTổng raw BQ       : {df1['sum_value_raw'].sum():.2f}")
    print(f"GA4 Console (28d) : 205.93")

# ── 2. Chi tiết từng transaction của renew event ─────────────────────────────
print("\n" + "=" * 70)
print("2. CHI TIẾT app_store_subscription_renew")
print("=" * 70)

q2 = f"""
SELECT
  event_date,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', TIMESTAMP_MICROS(event_timestamp), 'Asia/Ho_Chi_Minh') AS ts_vn,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'currency')       AS currency,
  ROUND(COALESCE(
    (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value'),
    (SELECT value.float_value  FROM UNNEST(event_params) WHERE key = 'value'),
    0
  ), 4)                                                                               AS value,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'product_id')     AS product_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'transaction_id') AS transaction_id,
  user_pseudo_id
FROM `ios-face-scanner.analytics_540983063.events_intraday_*`
WHERE event_name = 'app_store_subscription_renew'
  AND _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
ORDER BY event_date, event_timestamp
"""

df2 = client.query(q2).to_dataframe()
if df2.empty:
    print("Không có event app_store_subscription_renew trong intraday tables!")
    print("→ Event này có thể chỉ có trong finalized tables (events_YYYYMMDD)")
else:
    print(df2.to_string(index=False))
    print(f"\nTổng: {len(df2)} renewals, sum value = {df2['value'].sum():.2f}")

# ── 3. Kiểm tra finalized tables có tồn tại không ───────────────────────────
print("\n" + "=" * 70)
print("3. KIỂM TRA FINALIZED TABLES (events_YYYYMMDD)")
print("=" * 70)

dataset_ref = bigquery.DatasetReference("ios-face-scanner", "analytics_540983063")
all_tables = sorted([t.table_id for t in client.list_tables(dataset_ref)])
finalized = [t for t in all_tables if t.startswith("events_2")]
intraday  = [t for t in all_tables if "intraday" in t]

print(f"Finalized tables (events_YYYYMMDD) : {len(finalized)}")
print(f"Intraday tables                    : {len(intraday)}")
if finalized:
    print("Finalized:", finalized)
else:
    print("→ KHÔNG CÓ finalized table nào!")
    print("→ App mới được kết nối BigQuery export, data chỉ có trong intraday")
    print("→ GA4 Console lấy revenue từ nguồn khác (App Store Connect), không phải BQ event params")
