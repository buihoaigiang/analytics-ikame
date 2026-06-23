import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json"
client = bigquery.Client(project="team-begamob")

# ── 1. Timing: bao nhiêu phút/giờ/ngày sau purchase thì cancel? ─────────────
TIMING_QUERY = """
WITH base AS (
    SELECT
        'iOS' AS platform,
        CAST(_subscription_purchased_at_ AS INT64) AS purchased_at,
        CAST(_created_at_ AS INT64)                AS cancelled_at,
        _subscription_product_id_
    FROM `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ = 'cancellation'
      AND _country_ = 'us'

    UNION ALL

    SELECT
        'Android' AS platform,
        CAST(_subscription_purchased_at_ AS INT64) AS purchased_at,
        CAST(_created_at_ AS INT64)                AS cancelled_at,
        _subscription_product_id_
    FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ = 'cancellation'
      AND _country_ = 'us'
)
SELECT
    platform,
    _subscription_product_id_ AS product_id,
    ROUND((cancelled_at - purchased_at) / 3600.0, 2) AS hours_to_cancel,
    CASE
        WHEN (cancelled_at - purchased_at) < 3600        THEN '< 1 hour'
        WHEN (cancelled_at - purchased_at) < 86400       THEN '1h–24h'
        WHEN (cancelled_at - purchased_at) < 86400 * 3   THEN '1–3 days'
        WHEN (cancelled_at - purchased_at) < 86400 * 7   THEN '3–7 days'
        ELSE '> 7 days'
    END AS timing_bucket
FROM base
"""

print("Fetching timing data (US only)...")
df_timing = client.query(TIMING_QUERY).to_dataframe()

# Timing distribution
timing_dist = (df_timing.groupby(["platform", "timing_bucket"])
               .size().reset_index(name="count"))
timing_total = timing_dist.groupby("platform")["count"].transform("sum")
timing_dist["pct"] = (timing_dist["count"] / timing_total * 100).round(1)

print("\n── TIMING DISTRIBUTION (US, Jun 2026) ──")
print(timing_dist.to_string(index=False))

# ── 2. Denominator check: cancel rate theo từng cách tính ───────────────────
RATE_QUERY = """
SELECT platform, event_type, count
FROM (
    SELECT 'iOS' AS platform, _subscription_event_type_ AS event_type, COUNT(*) AS count
    FROM `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _country_ = 'us'
    GROUP BY 2
    UNION ALL
    SELECT 'Android', _subscription_event_type_, COUNT(*)
    FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _country_ = 'us'
    GROUP BY 2
)
ORDER BY platform, count DESC
"""

print("\nFetching event counts (US only)...")
df_rate = client.query(RATE_QUERY).to_dataframe()
print("\n── EVENT COUNTS (US, Jun 2026) ──")
print(df_rate.to_string(index=False))

# Tính cancel rate theo 2 cách
for platform in ["iOS", "Android"]:
    sub = df_rate[df_rate["platform"] == platform].set_index("event_type")["count"]
    cancel    = sub.get("cancellation", 0)
    activate  = sub.get("activation", 0)
    trial     = sub.get("trial_started", 0)
    discount  = sub.get("discounted_offer", 0)

    rate_v1 = cancel / activate * 100 if activate else float("nan")
    rate_v2 = cancel / (activate + trial) * 100 if (activate + trial) else float("nan")
    rate_v3 = cancel / (activate + trial + discount) * 100 if (activate + trial + discount) else float("nan")

    print(f"\n{platform}:")
    print(f"  cancel/activation              = {rate_v1:.1f}%")
    print(f"  cancel/(activation+trial)      = {rate_v2:.1f}%")
    print(f"  cancel/(activation+trial+disc) = {rate_v3:.1f}%")

# ── 3. Product breakdown: trial vs no-trial ──────────────────────────────────
PRODUCT_QUERY = """
SELECT platform, product_id, event_type, cnt FROM (
    SELECT 'iOS' AS platform, _subscription_product_id_ AS product_id,
           _subscription_event_type_ AS event_type, COUNT(*) AS cnt
    FROM `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ IN ('activation','trial_started','cancellation','discounted_offer')
      AND _country_ = 'us'
    GROUP BY 2,3
    UNION ALL
    SELECT 'Android', _subscription_product_id_,
           _subscription_event_type_, COUNT(*)
    FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-06-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ IN ('activation','trial_started','cancellation','discounted_offer')
      AND _country_ = 'us'
    GROUP BY 2,3
)
ORDER BY platform, cnt DESC
"""

print("\nFetching product breakdown (US only)...")
df_prod = client.query(PRODUCT_QUERY).to_dataframe()
print("\n── PRODUCT × EVENT BREAKDOWN (US) ──")
print(df_prod.to_string(index=False))

# ── 4. Chart: timing distribution ───────────────────────────────────────────
BUCKET_ORDER = ["< 1 hour", "1h–24h", "1–3 days", "3–7 days", "> 7 days"]
timing_dist["timing_bucket"] = pd.Categorical(timing_dist["timing_bucket"], categories=BUCKET_ORDER, ordered=True)
timing_dist = timing_dist.sort_values("timing_bucket")

fig = make_subplots(rows=1, cols=2, subplot_titles=["iOS — Cancel timing (US)", "Android — Cancel timing (US)"])
COLORS = ["#2C3E50", "#E74C3C", "#2980B9", "#27AE60", "#F39C12"]

for i, platform in enumerate(["iOS", "Android"], start=1):
    sub = timing_dist[timing_dist["platform"] == platform]
    fig.add_trace(go.Bar(
        x=sub["timing_bucket"], y=sub["pct"],
        text=sub["pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        marker_color=COLORS,
        name=platform,
        showlegend=False,
    ), row=1, col=i)

fig.update_layout(
    title="Khi nào user cancel subscription? (tính từ lúc mua) — US only",
    paper_bgcolor="#ECF0F1", plot_bgcolor="#ECF0F1",
    font=dict(color="#2C3E50"),
    height=450,
)
fig.update_yaxes(title_text="% cancels", ticksuffix="%")

out_path = r"c:\Users\admin\Desktop\analytics-ikame\20260623_android-ios-comparison\verify-cancel-android-vs-ios\data\outputs\cancel_timing.html"
fig.write_html(out_path)
print(f"\nChart saved → {out_path}")
