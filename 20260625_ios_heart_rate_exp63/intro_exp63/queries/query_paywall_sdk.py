"""
Phân tích điểm chạm paywall từ SDK_PREMIUM_TRACK
- Source: iOS_Heart_Rate_CACHED_Events_02.SDK_PREMIUM_TRACK (18-21/06/2026)
- Join với firebase_ab_testing_corhort_all_metrics để lấy experiment_variant
- Output: view / select / purchase CVR theo (screen_from, screen, variant)
- Note: max_date = 2026-06-21 → Rollback users (install >= 22/06) chưa có data
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

CRED_PATH = r'c:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json'

with open(CRED_PATH) as f:
    info = json.load(f)
creds = Credentials(token=None, refresh_token=info['refresh_token'],
    client_id=info['client_id'], client_secret=info['client_secret'],
    token_uri='https://oauth2.googleapis.com/token')
client = bigquery.Client(credentials=creds, project='team-begamob')

q = """
WITH list_ab AS (
  SELECT DISTINCT experiment_variant, LOWER(user_pseudo_id) AS uid
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_03.firebase_ab_testing_corhort_all_metrics`
  WHERE install_date >= '2026-06-01' AND experiment = 'firebase_exp_63'
),
_ft AS (
  SELECT * EXCEPT (params_screen_from),
    CASE WHEN params_action_name = 'open' THEN
      COALESCE(params_screen_from, '')
    END AS params_screen_from
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_02.SDK_PREMIUM_TRACK`
  WHERE event_date BETWEEN '2026-06-18' AND CURRENT_DATE('UTC+7')
),
-- Carry-forward screen_from for non-open events
_f AS (
  SELECT * EXCEPT (params_screen_from),
    CASE WHEN params_screen_from IS NULL
      THEN LAST_VALUE(params_screen_from IGNORE NULLS) OVER (
        PARTITION BY user_pseudo_id ORDER BY event_timestamp
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      ELSE params_screen_from
    END AS params_screen_from
  FROM _ft
),
_j AS (
  SELECT f.*, ab.experiment_variant,
    CASE ab.experiment_variant WHEN '0' THEN 'Baseline' ELSE 'FlowIntro14' END AS variant_label
  FROM _f f
  INNER JOIN list_ab ab ON LOWER(f.user_pseudo_id) = ab.uid
)
SELECT
  params_screen_from                                                             AS screen_from,
  params_premium_screen_name                                                     AS screen,
  variant_label,
  COUNT(DISTINCT IF(params_action_name='open',             user_pseudo_id,NULL)) AS screen_view,
  COUNT(DISTINCT IF(params_action_name='select_product',   user_pseudo_id,NULL)) AS select_product,
  COUNT(DISTINCT IF(params_action_name='finish_purchase' AND params_purchase_status='success',
                                                           user_pseudo_id,NULL)) AS purchase_success
FROM _j
GROUP BY 1,2,3
ORDER BY screen_from, screen, variant_label
"""

rows = list(client.query(q).result())

# Pivot theo (screen_from, screen) x variant
data = {}
for r in rows:
    key = (r['screen_from'] or '', r['screen'] or '')
    v   = r['variant_label']
    if key not in data:
        data[key] = {}
    data[key][v] = {
        'view': int(r['screen_view']),
        'sel':  int(r['select_product']),
        'pur':  int(r['purchase_success']),
    }

def pct(a, b):
    return f"{a/b*100:.1f}%" if b else "—"

VARIANTS = ['Baseline', 'FlowIntro14']

# 3 paywall contexts chính
print("\n" + "="*60)
print("FOCUS: 3 PAYWALL CONTEXTS (exp63 users only)")
print("="*60)

contexts = [
    ('splash',        'subscribe5',   'Intro paywall lần 1 (Baseline: step 14 / V1: step 8)'),
    ('splash',        'subscribe5_2', 'Intro paywall lần 2 (step 15, cả 2 luồng)'),
    ('measure_result','subscribe5',   'In-app paywall từ màn đo nhịp tim'),
]

for sfrom, sname, label in contexts:
    vdict = data.get((sfrom, sname), {})
    print(f"\n{label}  [{sfrom} → {sname}]")
    for v in VARIANTS:
        d = vdict.get(v, {'view':0,'sel':0,'pur':0})
        print(f"  {v:<14}: view={d['view']:>5,}  select={d['sel']:>5,}  purchase={d['pur']:>4,}"
              f"  CVR/sel={pct(d['pur'],d['sel']):>7}  CVR/view={pct(d['pur'],d['view']):>7}")

# Total purchases
print("\n=== Total Purchases ===")
for sfrom, sname, label in contexts:
    vdict = data.get((sfrom, sname), {})
    for v in VARIANTS:
        d = vdict.get(v, {'pur':0})
        print(f"  {label:<45} {v:<14}: {d['pur']:>4} purchases")
