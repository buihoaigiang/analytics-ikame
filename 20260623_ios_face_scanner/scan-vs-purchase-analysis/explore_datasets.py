import os
import json
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

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

print("=== DATASETS ===")
for ds in client.list_datasets():
    name = ds.dataset_id
    if "face" in name.lower() or "scanner" in name.lower() or "analytics" in name.lower():
        print(f"  {name}")

print("\n=== ALL DATASETS (filter: contains 'face' or 'scan' or 'analytics') ===")
all_ds = [ds.dataset_id for ds in client.list_datasets()]
for name in sorted(all_ds):
    print(f"  {name}")
