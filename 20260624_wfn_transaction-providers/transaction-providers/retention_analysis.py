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
    token=c.get("access_token"),
    refresh_token=c.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=c.get("client_id"),
    client_secret=c.get("client_secret"),
)
client = bigquery.Client(project=PROJECT, credentials=creds)

# ─── 1. Toàn bộ transactionType values ────────────────────────────────────────
print("=" * 70)
print("1. ALL transactionType VALUES")
print("=" * 70)
q = f"SELECT DISTINCT transactionType, COUNT(*) n FROM {TABLE} GROUP BY 1 ORDER BY n DESC"
print(client.query(q).to_dataframe().to_string(index=False))

# ─── 2. Mỗi userId có bao nhiêu records ───────────────────────────────────────
print("\n" + "=" * 70)
print("2. SO RECORDS PER userId (de check xem co renewal an danh hay khong)")
print("=" * 70)
q2 = f"""
SELECT
  n_events,
  COUNT(*) AS so_user
FROM (
  SELECT userId, COUNT(*) AS n_events FROM {TABLE}
  WHERE userId IS NOT NULL
  GROUP BY userId
)
GROUP BY 1 ORDER BY 1
"""
print(client.query(q2).to_dataframe().to_string(index=False))

# ─── 3. Xem user có nhiều records nhất ───────────────────────────────────────
print("\n" + "=" * 70)
print("3. USERS CO NHIEU EVENTS (co the la renewal an danh?)")
print("=" * 70)
q3 = f"""
SELECT
  userId,
  COUNT(*) AS n_events,
  STRING_AGG(transactionType, ', ' ORDER BY createdAt) AS event_sequence,
  MIN(DATE(createdAt)) AS first_date,
  MAX(DATE(createdAt)) AS last_date,
  ROUND(SUM(amount_real), 2) AS total_paid
FROM {TABLE}
WHERE userId IS NOT NULL
GROUP BY userId
HAVING n_events > 1
ORDER BY n_events DESC
LIMIT 20
"""
df3 = client.query(q3).to_dataframe()
print(df3.to_string(index=False))

# ─── 4. Check nextBillingDate: proxy cho "sẽ renew" ──────────────────────────
print("\n" + "=" * 70)
print("4. nextBillingDate ANALYSIS (proxy renew)")
print("=" * 70)
q4 = f"""
SELECT
  transactionType,
  COUNT(*)                                       AS total,
  COUNT(nextBillingDate)                         AS co_nextBillingDate,
  COUNT(CASE WHEN nextBillingDate IS NULL THEN 1 END) AS khong_co_nextBillingDate
FROM {TABLE}
GROUP BY 1
ORDER BY total DESC
"""
print(client.query(q4).to_dataframe().to_string(index=False))

# ─── 5. Retention dùng nextBillingDate làm proxy ─────────────────────────────
print("\n" + "=" * 70)
print("5. RETENTION = users with nextBillingDate / total first_purchase (cohort by date)")
print("   Logic: neu nextBillingDate != NULL -> user se duoc tinh phi lan sau -> da renew")
print("=" * 70)
q5 = f"""
WITH fp AS (
  SELECT
    DATE(createdAt)          AS cohort_date,
    userId,
    nextBillingDate,
    amount_real,
    plan_name,
    provider
  FROM {TABLE}
  WHERE transactionType = 'first_purchase'
)
SELECT
  cohort_date,
  provider,
  plan_name,
  COUNT(DISTINCT userId)                                              AS total_first_purchase,
  COUNT(DISTINCT CASE WHEN nextBillingDate IS NOT NULL THEN userId END) AS co_nextBilling,
  COUNT(DISTINCT CASE WHEN nextBillingDate IS NULL     THEN userId END) AS khong_co_nextBilling,
  ROUND(
    COUNT(DISTINCT CASE WHEN nextBillingDate IS NOT NULL THEN userId END) * 100.0
    / NULLIF(COUNT(DISTINCT userId), 0), 1
  ) AS retention_pct_proxy,
  ROUND(SUM(amount_real), 2) AS total_revenue
FROM fp
GROUP BY 1, 2, 3
ORDER BY cohort_date DESC, total_first_purchase DESC
"""
print(client.query(q5).to_dataframe().to_string(index=False))

# ─── 6. Revenue hôm qua (ngày gần nhất) tổng hợp ────────────────────────────
print("\n" + "=" * 70)
print("6. REVENUE SUMMARY NGAY GAN NHAT (2026-06-23)")
print("=" * 70)
q6 = f"""
SELECT
  DATE(createdAt) AS ngay,
  provider,
  payment_gateway,
  transactionType,
  COUNT(*) AS giao_dich,
  ROUND(SUM(amount_real), 2) AS revenue
FROM {TABLE}
WHERE DATE(createdAt) = '2026-06-23'
GROUP BY 1,2,3,4
ORDER BY revenue DESC
"""
df6 = client.query(q6).to_dataframe()
print(df6.to_string(index=False))
total = df6[df6['transactionType']=='first_purchase']['revenue'].sum()
print(f"\n  -> Revenue first_purchase ngay 2026-06-23: ${total:.2f}")
print(f"  -> Tong tat ca: ${df6['revenue'].sum():.2f}")
