import sys
sys.stdout.reconfigure(encoding="utf-8")
import os, json
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

CRED_PATH = os.path.join(os.path.dirname(__file__), "gcloud_credentials.json")
with open(CRED_PATH) as f:
    cred_data = json.load(f)

creds = Credentials(
    token=None,
    refresh_token=cred_data["refresh_token"],
    client_id=cred_data["client_id"],
    client_secret=cred_data["client_secret"],
    token_uri="https://oauth2.googleapis.com/token",
)
client = bigquery.Client(project="team-begamob", credentials=creds)

QUERY = """
SELECT
  ep.key,
  ep.value.string_value,
  ep.value.int_value,
  ep.value.float_value,
  COUNT(*) AS cnt
FROM `ios-face-scanner.analytics_540983063.events_*`,
UNNEST(event_params) AS ep
WHERE event_name = 'ft_face_scan'
GROUP BY 1, 2, 3, 4
ORDER BY ep.key, cnt DESC
LIMIT 100
"""

df = client.query(QUERY).to_dataframe()
print(df.to_string(index=False))
