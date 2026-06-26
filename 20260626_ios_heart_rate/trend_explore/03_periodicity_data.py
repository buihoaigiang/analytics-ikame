"""
Pull dimensional data from BQ for periodicity analysis.
Saves CSVs: dim_tier.csv, dim_traffic_source_medium.csv
(country removed — analyzed via tier instead)

Tier logic: Tier01 is split into 'United_States' vs 'Tier01_excl_US'
Traffic source: CPP_* remapping to FacebookW2A is done in 04_periodicity_analysis.py
"""

import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

import google.auth
from google.cloud import bigquery

PROJECT     = "team-begamob"
DATASET     = "iOS_Heart_Rate_CACHED_Events_03"
DATE_FROM   = "2026-01-01"
DATE_TO     = "2026-06-25"
COHORT_DAY  = 60
DATA_SOURCE = "Adjust"

CREDENTIAL_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "gcloud_credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "gcloud_credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "..", "gcloud_credentials.json"),
    r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json",
]
CRED_PATH = next((p for p in CREDENTIAL_CANDIDATES if os.path.exists(p)), None)
if not CRED_PATH:
    sys.exit("gcloud_credentials.json not found.")

creds, _ = google.auth.load_credentials_from_file(CRED_PATH)
client   = bigquery.Client(project=PROJECT, credentials=creds)

OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Query 1: Tier (with US extracted from Tier01) ─────────────────────────────
print("\nQuerying dim=tier (US extracted from Tier01) ...")
query_tier = f"""
WITH installs AS (
  SELECT
    install_date,
    CASE
      WHEN tier = 'Tier01' AND country = 'United States' THEN 'United_States'
      ELSE tier
    END AS segment,
    SUM(new_users) AS new_users
  FROM `{PROJECT}.{DATASET}.sdk_iap_installs`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    AND data_source = '{DATA_SOURCE}'
  GROUP BY install_date, segment
),
pay_start AS (
  SELECT
    install_date,
    CASE
      WHEN tier = 'Tier01' AND country = 'United States' THEN 'United_States'
      ELSE tier
    END AS segment,
    SUM(purchase_start_users) AS purchase_start_amt
  FROM `{PROJECT}.{DATASET}.sdk_iap_pay_start_cohort_all_product`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    AND number_day_install = {COHORT_DAY}
    AND data_source        = '{DATA_SOURCE}'
  GROUP BY install_date, segment
)
SELECT
  i.install_date,
  i.segment,
  i.new_users,
  IFNULL(ps.purchase_start_amt, 0)                           AS purchase_start_amt,
  SAFE_DIVIDE(IFNULL(ps.purchase_start_amt, 0), i.new_users) AS pay_rate_start
FROM installs i
LEFT JOIN pay_start ps
  ON i.install_date = ps.install_date
  AND i.segment     = ps.segment
ORDER BY i.install_date, i.segment
"""
df_tier = client.query(query_tier).to_dataframe()
tier_path = os.path.join(OUT_DIR, "dim_tier.csv")
df_tier.to_csv(tier_path, index=False, encoding="utf-8-sig")
print(f"  {len(df_tier)} rows, segments: {sorted(df_tier['segment'].unique().tolist())} -> {tier_path}")

# ── Query 2: Traffic Source Medium ────────────────────────────────────────────
print("\nQuerying dim=traffic_source_medium ...")
query_tsm = f"""
WITH installs AS (
  SELECT
    install_date,
    traffic_source_medium,
    SUM(new_users) AS new_users
  FROM `{PROJECT}.{DATASET}.sdk_iap_installs`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    AND data_source = '{DATA_SOURCE}'
  GROUP BY install_date, traffic_source_medium
),
pay_start AS (
  SELECT
    install_date,
    traffic_source_medium,
    SUM(purchase_start_users) AS purchase_start_amt
  FROM `{PROJECT}.{DATASET}.sdk_iap_pay_start_cohort_all_product`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    AND number_day_install = {COHORT_DAY}
    AND data_source        = '{DATA_SOURCE}'
  GROUP BY install_date, traffic_source_medium
)
SELECT
  i.install_date,
  i.traffic_source_medium                                    AS segment,
  i.new_users,
  IFNULL(ps.purchase_start_amt, 0)                           AS purchase_start_amt,
  SAFE_DIVIDE(IFNULL(ps.purchase_start_amt, 0), i.new_users) AS pay_rate_start
FROM installs i
LEFT JOIN pay_start ps
  ON i.install_date          = ps.install_date
  AND i.traffic_source_medium = ps.traffic_source_medium
ORDER BY i.install_date, i.traffic_source_medium
"""
df_tsm = client.query(query_tsm).to_dataframe()
tsm_path = os.path.join(OUT_DIR, "dim_traffic_source_medium.csv")
df_tsm.to_csv(tsm_path, index=False, encoding="utf-8-sig")
print(f"  {len(df_tsm)} rows, {df_tsm['segment'].nunique()} segments -> {tsm_path}")

print("\nDone.")
