"""
Schema check for 3 tables used in pay rate analysis.
Run this first to confirm column names before running the main chart script.
"""

import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

import google.auth
from google.cloud import bigquery

CREDENTIAL_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "gcloud_credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "gcloud_credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "..", "gcloud_credentials.json"),
    r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json",
]
CREDENTIAL_PATH = next((p for p in CREDENTIAL_CANDIDATES if os.path.exists(p)), None)
if not CREDENTIAL_PATH:
    sys.exit("gcloud_credentials.json not found. Copy it into the project folder.")
PROJECT = "team-begamob"
DATASET = "iOS_Heart_Rate_CACHED_Events_03"

TABLES = [
    "sdk_iap_installs",
    "sdk_iap_pay_start_cohort_all_product",
    "sdk_iap_conversion_cohort_all_product",
]

creds, _ = google.auth.load_credentials_from_file(CREDENTIAL_PATH)
client = bigquery.Client(project=PROJECT, credentials=creds)

for table_name in TABLES:
    full_id = f"{PROJECT}.{DATASET}.{table_name}"
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")
    try:
        table = client.get_table(full_id)
        for field in table.schema:
            print(f"  {field.name:<45} {field.field_type}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDone.")
