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

# ─── Q1: Revenue hôm nay ──────────────────────────────────────────────────────
print("=" * 70)
print("Q1: REVENUE HOM NAY (2026-06-24) PHAN TICH DA CHIEU")
print("=" * 70)

q1 = f"""
SELECT
  DATE(createdAt) AS ngay,
  provider,
  payment_gateway,
  transactionType,
  plan_name,
  project_domain,
  COUNT(*)                        AS so_giao_dich,
  ROUND(SUM(amount_real), 2)      AS tong_revenue,
  ROUND(AVG(amount_real), 2)      AS avg_revenue
FROM {TABLE}
WHERE DATE(createdAt) = '2026-06-24'
GROUP BY 1,2,3,4,5,6
ORDER BY tong_revenue DESC
"""
df1 = client.query(q1).to_dataframe()
if df1.empty:
    print("Khong co du lieu hom nay (2026-06-24). Thu xem ngay gan nhat...")
    q1b = f"""
    SELECT
      DATE(createdAt) AS ngay,
      provider,
      payment_gateway,
      transactionType,
      plan_name,
      project_domain,
      COUNT(*)                       AS so_giao_dich,
      ROUND(SUM(amount_real), 2)     AS tong_revenue
    FROM {TABLE}
    WHERE DATE(createdAt) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY 1,2,3,4,5,6
    ORDER BY ngay DESC, tong_revenue DESC
    LIMIT 50
    """
    df1 = client.query(q1b).to_dataframe()

print(df1.to_string(index=False))

# Tổng hợp nhanh
print("\n--- TONG HOP NHANH ---")
q1c = f"""
SELECT
  DATE(createdAt) AS ngay,
  COUNT(*)                   AS so_giao_dich,
  ROUND(SUM(amount_real), 2) AS tong_revenue
FROM {TABLE}
WHERE DATE(createdAt) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY 1
ORDER BY 1 DESC
"""
df1c = client.query(q1c).to_dataframe()
print(df1c.to_string(index=False))

# Distinct values
print("\n--- DISTINCT VALUES ---")
q_dist = f"""
SELECT
  'transactionType' AS col, transactionType AS val, COUNT(*) AS n
FROM {TABLE}
GROUP BY 2
UNION ALL
SELECT 'provider', provider, COUNT(*) FROM {TABLE} GROUP BY 2
UNION ALL
SELECT 'payment_gateway', payment_gateway, COUNT(*) FROM {TABLE} GROUP BY 2
ORDER BY col, n DESC
"""
df_dist = client.query(q_dist).to_dataframe()
print(df_dist.to_string(index=False))


# ─── Q2: Retention subscription ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("Q2: RETENTION SUBSCRIPTION = renewals / first_purchase (cung cohort)")
print("=" * 70)

# Check xem transactionType có value gì
# Dùng userId để join cohort: first_purchase -> renewals cùng user
# Cohort = ngày first_purchase của user đó

q2 = f"""
WITH first_purchase AS (
  SELECT
    userId,
    MIN(DATE(createdAt)) AS cohort_date,
    COUNT(*) AS n_first  -- nên là 1 per user nếu đúng logic
  FROM {TABLE}
  WHERE LOWER(transactionType) LIKE '%first%'
     OR LOWER(transactionType) LIKE '%initial%'
     OR LOWER(transactionType) LIKE '%new%'
     OR LOWER(transactionType) LIKE '%purchase%'
  GROUP BY userId
),
renewals AS (
  SELECT
    userId,
    DATE(createdAt) AS renewal_date,
    amount_real
  FROM {TABLE}
  WHERE LOWER(transactionType) LIKE '%renew%'
     OR LOWER(transactionType) LIKE '%rebill%'
     OR LOWER(transactionType) LIKE '%subscription%'
),
cohort_joined AS (
  SELECT
    fp.cohort_date,
    fp.userId,
    r.renewal_date,
    DATE_DIFF(r.renewal_date, fp.cohort_date, DAY) AS days_after,
    r.amount_real
  FROM first_purchase fp
  LEFT JOIN renewals r ON fp.userId = r.userId
)
SELECT
  cohort_date,
  COUNT(DISTINCT userId)                                                    AS total_first_purchase_users,
  COUNT(DISTINCT CASE WHEN renewal_date IS NOT NULL THEN userId END)        AS users_with_renewal,
  COUNT(renewal_date)                                                       AS total_renewals,
  ROUND(
    COUNT(DISTINCT CASE WHEN renewal_date IS NOT NULL THEN userId END) * 100.0
    / NULLIF(COUNT(DISTINCT userId), 0), 1
  )                                                                         AS retention_pct,
  ROUND(SUM(CASE WHEN renewal_date IS NOT NULL THEN amount_real END), 2)   AS renewal_revenue
FROM cohort_joined
GROUP BY cohort_date
ORDER BY cohort_date DESC
LIMIT 60
"""

try:
    df2 = client.query(q2).to_dataframe()
    print(df2.to_string(index=False))
except Exception as e:
    print(f"Query Q2 loi: {e}")
    print("\nThu xem transactionType raw values...")
    q_types = f"SELECT DISTINCT transactionType, COUNT(*) AS n FROM {TABLE} GROUP BY 1 ORDER BY n DESC LIMIT 20"
    df_types = client.query(q_types).to_dataframe()
    print(df_types.to_string(index=False))
