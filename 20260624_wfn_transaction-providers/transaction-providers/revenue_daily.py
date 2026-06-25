import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2.credentials import Credentials
from google.cloud import bigquery
import pandas as pd

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

q = f"""
SELECT
  DATE(createdAt)            AS date,
  provider,
  payment_gateway,
  transactionType,
  plan_name,
  COUNT(*)                        AS transactions,
  COUNT(DISTINCT userId)          AS unique_users,
  ROUND(SUM(amount_real), 2)      AS revenue
FROM {TABLE}
WHERE transactionType = 'first_purchase'   -- chỉ tính revenue thực
GROUP BY 1,2,3,4,5
ORDER BY 1, revenue DESC
"""

df = client.query(q).to_dataframe()
print(df.to_string(index=False))

print("\n--- DAILY TOTAL ---")
daily = df.groupby("date")[["transactions","revenue"]].sum().reset_index()
print(daily.to_string(index=False))
