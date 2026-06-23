import os
import pandas as pd
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json"
PROJECT = "team-begamob"

client = bigquery.Client(project=PROJECT)

# ── 1. Schema khám phá: xem các cột liên quan subscription ──────────────────
SCHEMA_QUERY = """
SELECT column_name, data_type
FROM `team-begamob.MMP_Adjust_RawData.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN (
    'iOS_Heart_Rate_Raw_Export_PARTITION',
    'Android_Heart_Rate_Raw_Export_PARTITION'
)
AND LOWER(column_name) LIKE '%subscription%'
ORDER BY table_name, column_name
"""

print("=" * 60)
print("SUBSCRIPTION-RELATED COLUMNS")
print("=" * 60)
df_schema = client.query(SCHEMA_QUERY).to_dataframe()
print(df_schema.to_string(index=False))

# ── 2. Sample 5 dòng cancel event mỗi platform ──────────────────────────────
for platform, table in [
    ("iOS", "iOS_Heart_Rate_Raw_Export_PARTITION"),
    ("Android", "Android_Heart_Rate_Raw_Export_PARTITION"),
]:
    q = f"""
    SELECT *
    FROM `team-begamob.MMP_Adjust_RawData.{table}`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ = 'cancellation'
    LIMIT 5
    """
    print(f"\n{'=' * 60}")
    print(f"SAMPLE CANCEL ROWS — {platform}")
    print("=" * 60)
    df = client.query(q).to_dataframe()
    if df.empty:
        print("  No rows found")
    else:
        # In tên cột + giá trị sample
        for col in df.columns:
            vals = df[col].dropna().unique()[:3]
            if len(vals) > 0:
                print(f"  {col}: {list(vals)}")

# ── 3. Đếm tổng cancel vs tổng subscription event mỗi platform ──────────────
print("\n" + "=" * 60)
print("CANCEL COUNT vs TOTAL SUBSCRIPTION EVENTS")
print("=" * 60)

for platform, table in [
    ("iOS", "iOS_Heart_Rate_Raw_Export_PARTITION"),
    ("Android", "Android_Heart_Rate_Raw_Export_PARTITION"),
]:
    q = f"""
    SELECT
        _subscription_event_type_,
        COUNT(*) AS cnt
    FROM `team-begamob.MMP_Adjust_RawData.{table}`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
    GROUP BY 1
    ORDER BY cnt DESC
    """
    df = client.query(q).to_dataframe()
    print(f"\n{platform}:")
    print(df.to_string(index=False))
