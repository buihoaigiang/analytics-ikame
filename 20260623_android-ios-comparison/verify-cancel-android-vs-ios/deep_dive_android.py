import os
import pandas as pd
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json"
client = bigquery.Client(project="team-begamob")

# Android: cancel event có subscription_cancelled_at_ không? So sánh với iOS
Q = """
SELECT
    'iOS' AS platform,
    _subscription_product_id_ AS product,
    _subscription_event_type_ AS event_type,
    _subscription_cancelled_at_,
    CAST(_subscription_purchased_at_ AS INT64) AS purchased_ts,
    CAST(_created_at_ AS INT64) AS event_ts,
    ROUND((CAST(_created_at_ AS INT64) - CAST(_subscription_purchased_at_ AS INT64)) / 86400.0, 2) AS days_to_cancel
FROM `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
  AND _activity_kind_ = 'subscription'
  AND _subscription_event_type_ = 'cancellation'
  AND _country_ = 'us'
LIMIT 10
"""
print("── iOS sample (US) ──")
df = client.query(Q).to_dataframe()
for _, row in df.iterrows():
    print(f"  product={row['product'][-30:]:30s}  days={row['days_to_cancel']:6.2f}  cancelled_at_field={row['_subscription_cancelled_at_']}")

Q2 = """
SELECT
    'Android' AS platform,
    _subscription_product_id_ AS product,
    _subscription_event_type_ AS event_type,
    _subscription_cancelled_at_,
    CAST(_subscription_purchased_at_ AS INT64) AS purchased_ts,
    CAST(_created_at_ AS INT64) AS event_ts,
    ROUND((CAST(_created_at_ AS INT64) - CAST(_subscription_purchased_at_ AS INT64)) / 86400.0, 2) AS days_to_cancel
FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
  AND _activity_kind_ = 'subscription'
  AND _subscription_event_type_ = 'cancellation'
  AND _country_ = 'us'
LIMIT 10
"""
print("\n── Android sample (US) ──")
df2 = client.query(Q2).to_dataframe()
for _, row in df2.iterrows():
    print(f"  product={row['product'][-35:]:35s}  days={row['days_to_cancel']:6.2f}  cancelled_at_field={row['_subscription_cancelled_at_']}")

# Discounted_offer trên Android: đây là subscriber mới hay cũ?
Q3 = """
SELECT
    _subscription_product_id_ AS product,
    _subscription_event_type_ AS event_type,
    COUNT(*) AS cnt,
    ROUND(AVG(CAST(_created_at_ AS INT64) - CAST(_installed_at_ AS INT64)) / 86400.0, 1) AS avg_days_since_install
FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
  AND _activity_kind_ = 'subscription'
  AND _subscription_event_type_ IN ('discounted_offer', 'activation', 'cancellation')
GROUP BY 1, 2
ORDER BY cnt DESC
LIMIT 20
"""
print("\n── Android: discounted_offer vs activation vs cancel ──")
df3 = client.query(Q3).to_dataframe()
print(df3.to_string(index=False))
