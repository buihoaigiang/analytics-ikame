import os
import sys
os.environ["PYTHONIOENCODING"] = "utf-8"

from google.oauth2 import service_account
from google.cloud import bigquery
import json

CRED_PATH = r"c:\Users\admin\Desktop\analytics-ikame\20260623_ios_face_scanner\scan-vs-purchase-analysis\gcloud_credentials.json"

with open(CRED_PATH) as f:
    cred_info = json.load(f)

cred_type = cred_info.get("type", "")
PROJECT = "team-begamob"
TABLE = "ikame-apps-dev.tracking_transaction_providers.transaction-providers"

if cred_type == "authorized_user":
    from google.oauth2.credentials import Credentials
    creds = Credentials(
        token=cred_info.get("access_token"),
        refresh_token=cred_info.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cred_info.get("client_id"),
        client_secret=cred_info.get("client_secret"),
    )
    client = bigquery.Client(project=PROJECT, credentials=creds)
else:
    creds = service_account.Credentials.from_service_account_file(CRED_PATH)
    client = bigquery.Client(project=PROJECT, credentials=creds)

# 1. Schema
print("=" * 60)
print("SCHEMA")
print("=" * 60)
table_ref = client.get_table(TABLE)
for field in table_ref.schema:
    print(f"  {field.name:40s} {field.field_type:15s} {field.mode}")

# 2. Sample rows
print("\n" + "=" * 60)
print("SAMPLE (5 rows)")
print("=" * 60)
q = f"SELECT * FROM `{TABLE}` LIMIT 5"
df = client.query(q).to_dataframe()
print(df.to_string())

# 3. Distinct values of key dims
print("\n" + "=" * 60)
print("DISTINCT COUNTS + DATE RANGE")
print("=" * 60)
q2 = f"""
SELECT
  COUNT(*) AS total_rows,
  MIN(CAST(event_date AS STRING)) AS min_date,
  MAX(CAST(event_date AS STRING)) AS max_date
FROM `{TABLE}`
LIMIT 1
"""
try:
    r = client.query(q2).to_dataframe()
    print(r.to_string())
except Exception as e:
    print(f"(date range query failed: {e})")
