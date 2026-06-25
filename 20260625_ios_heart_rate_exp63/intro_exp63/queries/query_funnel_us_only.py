"""
Funnel comparison: Baseline vs FlowIntro14_IAP_New vs Rollback
- Filter: session_number=1, country='United States'
- Baseline/V1: users từ firebase_ab_testing_corhort_all_metrics (experiment='firebase_exp_63')
- Rollback: users install >= 2026-06-22 (ALL flows, không filter intro7)
- Output: funnel_data.json
"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

CRED_PATH = r'c:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json'
OUT_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'outputs', 'funnel_data.json')

with open(CRED_PATH) as f:
    info = json.load(f)
creds = Credentials(token=None, refresh_token=info['refresh_token'],
    client_id=info['client_id'], client_secret=info['client_secret'],
    token_uri='https://oauth2.googleapis.com/token')
client = bigquery.Client(credentials=creds, project='team-begamob')

CANONICAL = [
    'splash','sign_in_onboarding',
    'intro7_heart_measure','intro7_learn_more','intro7_track_stress',
    'intro7_blood_pressure','intro7_blood_sugar','intro7_check_apple_watch',
    'intro7_analyzing',
    'intro7_select_gender','intro7_select_age','intro7_select_height',
    'intro7_select_weight','intro7_question_health_issue','intro7_final_processing',
    'subscribe5_new','subscribe5_2',
    'new_home_v2','measure','how_we_take_measurements','new_mood_activity','measure_result2',
]

def run(label, where_ab, where_screen):
    q = f"""
    WITH ab AS ({where_ab}),
    screen AS (
      SELECT user_pseudo_id AS uid, screen_from
      FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
      WHERE session_number = 1
        AND country = 'United States'
        AND screen_from IS NOT NULL AND screen_from != ''
        {where_screen}
      GROUP BY 1, 2
    ),
    joined AS (
      SELECT s.screen_from, s.uid FROM screen s JOIN ab ON s.uid = ab.uid
    ),
    splash_total AS (
      SELECT COUNT(DISTINCT uid) AS n FROM joined WHERE screen_from = 'splash'
    )
    SELECT j.screen_from,
      COUNT(DISTINCT j.uid)                               AS users,
      MAX(t.n)                                            AS total_splash,
      ROUND(COUNT(DISTINCT j.uid)*100.0 / MAX(t.n), 2)  AS pct
    FROM joined j CROSS JOIN splash_total t
    GROUP BY 1 ORDER BY pct DESC
    """
    rows = list(client.query(q).result())
    pct = {r['screen_from']: float(r['pct']) for r in rows}
    n   = int(rows[0]['total_splash']) if rows else 0
    print(f"\n{label} (US only, n={n:,}):")
    for s in CANONICAL:
        p = pct.get(s)
        if p is not None:
            print(f"  {s:<42} {p:.2f}%")
    return pct, n

# Baseline (variant=0)
B_pct, T_B = run(
    'Baseline',
    """SELECT DISTINCT LOWER(user_pseudo_id) AS uid
       FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_03.firebase_ab_testing_corhort_all_metrics`
       WHERE install_date >= '2026-06-01' AND experiment = 'firebase_exp_63'
         AND experiment_variant = '0'""",
    ""
)

# FlowIntro14_IAP_New (variant=1)
V1_pct, T_V1 = run(
    'FlowIntro14',
    """SELECT DISTINCT LOWER(user_pseudo_id) AS uid
       FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_03.firebase_ab_testing_corhort_all_metrics`
       WHERE install_date >= '2026-06-01' AND experiment = 'firebase_exp_63'
         AND experiment_variant = '1'""",
    ""
)

# Rollback (install >= 22/06, US only, ALL flows)
RB_pct, T_RB = run(
    'Rollback US-only',
    """SELECT DISTINCT user_pseudo_id AS uid
       FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
       WHERE install_date >= '2026-06-22' AND country = 'United States'""",
    "AND install_date >= '2026-06-22'"
)

# Summary
print("\n\n=== FINAL COMPARISON — US Only ===")
print(f"{'Screen':<40} {'Baseline':>10} {'V1':>10} {'Rollback':>10}")
print("-"*75)
for s in CANONICAL:
    b  = B_pct.get(s);  v  = V1_pct.get(s);  rb = RB_pct.get(s)
    print(f"  {s:<38} {f'{b:.1f}%' if b else '-':>10} {f'{v:.1f}%' if v else '-':>10} {f'{rb:.1f}%' if rb else '-':>10}")
print(f"\nTotal n (US): Baseline={T_B:,}  V1={T_V1:,}  Rollback={T_RB:,}")

# Save
data = {'B': B_pct, 'T_B': T_B, 'V1': V1_pct, 'T_V1': T_V1, 'RB': RB_pct, 'T_RB': T_RB}
with open(OUT_PATH, 'w') as f:
    json.dump(data, f, indent=2)
print(f"\nSaved: {OUT_PATH}")
