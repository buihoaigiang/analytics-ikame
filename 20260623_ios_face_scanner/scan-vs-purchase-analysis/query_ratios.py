import os
import json
from google.oauth2.credentials import Credentials
from google.cloud import bigquery
import pandas as pd

os.environ["PYTHONIOENCODING"] = "utf-8"

CRED_PATH = os.path.join(os.path.dirname(__file__), "gcloud_credentials.json")
PROJECT = "team-begamob"

with open(CRED_PATH) as f:
    cred_data = json.load(f)

creds = Credentials(
    token=None,
    refresh_token=cred_data["refresh_token"],
    client_id=cred_data["client_id"],
    client_secret=cred_data["client_secret"],
    token_uri="https://oauth2.googleapis.com/token",
)

client = bigquery.Client(project=PROJECT, credentials=creds)

QUERY = """
WITH base AS (
  SELECT
    user_pseudo_id,
    event_name,
    -- convert microseconds → UTC+7
    DATE(TIMESTAMP_ADD(TIMESTAMP_MICROS(event_timestamp), INTERVAL 7 HOUR)) AS event_date
  FROM `ios-face-scanner.analytics_540983063.events_*`
  WHERE event_name IN ('ft_face_scan', 'in_app_purchase', 'first_open')
),

daily AS (
  SELECT
    event_date,
    COUNT(DISTINCT CASE WHEN event_name = 'first_open'      THEN user_pseudo_id END) AS users_install,
    COUNT(DISTINCT CASE WHEN event_name = 'ft_face_scan'    THEN user_pseudo_id END) AS users_facescan,
    COUNT(DISTINCT CASE WHEN event_name = 'in_app_purchase' THEN user_pseudo_id END) AS users_purchase
  FROM base
  GROUP BY event_date
)

SELECT
  event_date,
  users_install,
  users_facescan,
  users_purchase,
  ROUND(SAFE_DIVIDE(users_facescan, users_install) * 100, 2) AS pct_facescan_per_install,
  ROUND(SAFE_DIVIDE(users_purchase, users_install) * 100, 2) AS pct_purchase_per_install,
  ROUND(SAFE_DIVIDE(users_purchase, users_facescan) * 100, 2) AS pct_purchase_per_facescan
FROM daily
ORDER BY event_date
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

print("Running query...")
df = client.query(QUERY).to_dataframe()

print(f"\nResults ({len(df)} days):")
print(df.to_string(index=False))

OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "outputs")
os.makedirs(OUT_DIR, exist_ok=True)
out_path = os.path.join(OUT_DIR, "facescan_purchase_install_ratios.csv")
df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"\nSaved: {out_path}")
