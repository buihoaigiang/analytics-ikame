"""
So sánh revenue: GA4 raw data (BigQuery) vs Firebase Console screenshot
Screenshot: $142.20 tuần Jun 17-23, đỉnh $83.17 ngày Jun 22 (Monday)

NOTE: Chỉ có intraday tables nên dùng events_intraday_* thay vì events_*
_TABLE_SUFFIX sẽ là YYYYMMDD (phần sau intraday_)
"""
import pandas as pd
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

CRED_PATH = r"C:\Users\admin\Desktop\analytics-ikame\20260623_ios_face_scanner\scan-vs-purchase-analysis\gcloud_credentials.json"
PROJECT   = "team-begamob"
DATE_FROM = "20260611"
DATE_TO   = "20260624"

creds  = Credentials.from_authorized_user_file(CRED_PATH)
client = bigquery.Client(credentials=creds, project=PROJECT)

pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", "{:.2f}".format)

# ── 1. Summary revenue theo ngày ────────────────────────────────────────────
print("=" * 70)
print("1. REVENUE THEO NGÀY (in_app_purchase + purchase_sdk_event)")
print("=" * 70)

q_summary = f"""
SELECT
  event_date,
  event_name,
  COUNT(*)                                                              AS event_count,
  COUNT(DISTINCT
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'transaction_id')
  )                                                                     AS unique_tx,
  ROUND(SUM(
    COALESCE(
      (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value'),
      (SELECT value.float_value  FROM UNNEST(event_params) WHERE key = 'value'),
      0
    )
  ), 2)                                                                 AS sum_value,
  STRING_AGG(DISTINCT
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'currency')
  )                                                                     AS currencies
FROM `ios-face-scanner.analytics_540983063.events_intraday_*`
WHERE event_name IN ('in_app_purchase', 'purchase_sdk_event')
  AND _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
GROUP BY event_date, event_name
ORDER BY event_date, event_name
"""

df_sum = client.query(q_summary).to_dataframe()
if df_sum.empty:
    print("Không có data!")
else:
    print(df_sum.to_string(index=False))
    total = df_sum["sum_value"].sum()
    print(f"\nTổng raw BQ    : {total:.2f}")
    print(f"Firebase Cns   : 142.20  (Jun 17-23 theo screenshot)")
    print(f"Chênh lệch     : {total - 142.20:.2f}")

# ── 2. Tất cả params của 2 event để hiểu structure ─────────────────────────
print("\n" + "=" * 70)
print("2. TẤT CẢ PARAMS CỦA in_app_purchase")
print("=" * 70)

q_iap = f"""
SELECT
  event_date,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', TIMESTAMP_MICROS(event_timestamp), 'Asia/Ho_Chi_Minh') AS ts_vn,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'transaction_id') AS transaction_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'product_id')     AS product_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'currency')       AS currency,
  ROUND(COALESCE(
    (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value'),
    (SELECT value.float_value  FROM UNNEST(event_params) WHERE key = 'value'),
    0
  ), 2)                                                                               AS value,
  ROUND(COALESCE(
    (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'price'),
    (SELECT value.float_value  FROM UNNEST(event_params) WHERE key = 'price'),
    0
  ), 2)                                                                               AS price,
  COALESCE(
    (SELECT value.int_value    FROM UNNEST(event_params) WHERE key = 'quantity'),
    0
  )                                                                                   AS quantity,
  user_pseudo_id
FROM `ios-face-scanner.analytics_540983063.events_intraday_*`
WHERE event_name = 'in_app_purchase'
  AND _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
ORDER BY event_date, event_timestamp
"""

df_iap = client.query(q_iap).to_dataframe()
if df_iap.empty:
    print("Không có event in_app_purchase nào!")
else:
    print(df_iap.to_string(index=False))
    print(f"\nTổng value: {df_iap['value'].sum():.2f}")

# ── 3. Tất cả params của purchase_sdk_event ─────────────────────────────────
print("\n" + "=" * 70)
print("3. TẤT CẢ PARAMS CỦA purchase_sdk_event")
print("=" * 70)

q_sdk = f"""
SELECT
  event_date,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', TIMESTAMP_MICROS(event_timestamp), 'Asia/Ho_Chi_Minh') AS ts_vn,
  ep.key,
  COALESCE(
    ep.value.string_value,
    CAST(ep.value.int_value    AS STRING),
    CAST(ep.value.float_value  AS STRING),
    CAST(ep.value.double_value AS STRING)
  ) AS val
FROM `ios-face-scanner.analytics_540983063.events_intraday_*`,
  UNNEST(event_params) AS ep
WHERE event_name = 'purchase_sdk_event'
  AND _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
ORDER BY event_date, event_timestamp, ep.key
"""

df_sdk = client.query(q_sdk).to_dataframe()
if df_sdk.empty:
    print("Không có event purchase_sdk_event nào!")
else:
    print(df_sdk.to_string(index=False))
    print(f"\nTổng rows: {len(df_sdk)}")
