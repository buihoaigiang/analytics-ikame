import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2.credentials import Credentials
from google.cloud import bigquery

CRED_PATH = r"c:\Users\admin\Desktop\analytics-ikame\20260623_ios_face_scanner\scan-vs-purchase-analysis\gcloud_credentials.json"
PROJECT = "team-begamob"
TABLE   = "`ikame-apps-dev.tracking_transaction_providers.transaction-providers`"

with open(CRED_PATH) as f:
    c = json.load(f)

creds = Credentials(
    token=c.get("access_token"), refresh_token=c.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=c.get("client_id"), client_secret=c.get("client_secret"),
)
client = bigquery.Client(project=PROJECT, credentials=creds)

# Xem 1 user bị duplicate để hiểu cấu trúc raw
print("=" * 70)
print("DEEP DIVE: user 8a8a2c86 (6x first_purchase cung ngay) - co phai duplicate?")
print("=" * 70)
q = f"""
SELECT id, userId, transactionType, createdAt, nextBillingDate,
       amount_real, plan_name, price_id
FROM {TABLE}
WHERE userId = '8a8a2c86-a74d-45fd-8a22-c04beb6b744e'
ORDER BY createdAt
"""
df = client.query(q).to_dataframe()
print(df.to_string(index=False))

print("\n" + "=" * 70)
print("CHECK: id (PRIMARY KEY) co unique khong?")
print("=" * 70)
q2 = f"""
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT id) AS distinct_ids,
  COUNT(*) - COUNT(DISTINCT id) AS duplicate_ids
FROM {TABLE}
"""
print(client.query(q2).to_dataframe().to_string(index=False))

print("\n" + "=" * 70)
print("CANCEL records co amount_real > 0: refund hay status-log?")
print("=" * 70)
q3 = f"""
SELECT
  transactionType,
  COUNT(*) AS n,
  MIN(amount_real)  AS min_amount,
  MAX(amount_real)  AS max_amount,
  ROUND(SUM(amount_real), 2) AS sum_amount,
  ROUND(AVG(amount_real), 2) AS avg_amount,
  COUNT(CASE WHEN amount_real > 0 THEN 1 END) AS co_amount_duong,
  COUNT(CASE WHEN amount_real = 0 THEN 1 END) AS zero_amount,
  COUNT(CASE WHEN amount_real IS NULL THEN 1 END) AS null_amount
FROM {TABLE}
GROUP BY 1
"""
print(client.query(q3).to_dataframe().to_string(index=False))

print("\n" + "=" * 70)
print("nextBillingDate: phan bo thoi gian")
print("=" * 70)
q4 = f"""
SELECT
  transactionType,
  plan_name,
  DATE(nextBillingDate) AS next_billing_date,
  COUNT(*) AS n
FROM {TABLE}
WHERE nextBillingDate IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY transactionType, next_billing_date
LIMIT 40
"""
print(client.query(q4).to_dataframe().to_string(index=False))
