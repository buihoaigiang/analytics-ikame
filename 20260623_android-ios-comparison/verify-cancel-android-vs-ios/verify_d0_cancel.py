import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json"
client = bigquery.Client(project="team-begamob")

# ── Core: join start event → cancel event theo original_transaction_id ───────
# D0 = cancel xảy ra trong vòng 24h kể từ lúc subscription bắt đầu
# Mở rộng date range để có đủ Android data
D0_QUERY = """
WITH ios_starts AS (
    SELECT
        _subscription_original_transaction_id_ AS orig_txn,
        _adid_                                  AS adid,
        _subscription_event_type_               AS start_event,
        _subscription_product_id_               AS product,
        CAST(_created_at_ AS INT64)             AS start_ts,
        CAST(_installed_at_ AS INT64)           AS install_ts,
        _country_                               AS country
    FROM `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-01-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ IN ('activation', 'trial_started', 'discounted_offer')
),
ios_cancels AS (
    SELECT
        _subscription_original_transaction_id_ AS orig_txn,
        CAST(_created_at_ AS INT64)            AS cancel_ts
    FROM `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-01-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ = 'cancellation'
),
android_starts AS (
    SELECT
        _subscription_original_transaction_id_ AS orig_txn,
        _adid_                                  AS adid,
        _subscription_event_type_               AS start_event,
        _subscription_product_id_               AS product,
        CAST(_created_at_ AS INT64)             AS start_ts,
        CAST(_installed_at_ AS INT64)           AS install_ts,
        _country_                               AS country
    FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-01-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ IN ('activation', 'trial_started', 'discounted_offer')
),
android_cancels AS (
    SELECT
        _subscription_original_transaction_id_ AS orig_txn,
        CAST(_created_at_ AS INT64)            AS cancel_ts
    FROM `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION`
    WHERE TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-01-01")
      AND _activity_kind_ = 'subscription'
      AND _subscription_event_type_ = 'cancellation'
),
ios_joined AS (
    SELECT
        'iOS'    AS platform,
        s.adid, s.orig_txn, s.start_event, s.product, s.country,
        s.start_ts, s.install_ts,
        c.cancel_ts,
        (c.cancel_ts - s.start_ts)   AS secs_start_to_cancel,
        (s.start_ts  - s.install_ts) AS secs_install_to_start
    FROM ios_starts s
    LEFT JOIN ios_cancels c USING (orig_txn)
),
android_joined AS (
    SELECT
        'Android' AS platform,
        s.adid, s.orig_txn, s.start_event, s.product, s.country,
        s.start_ts, s.install_ts,
        c.cancel_ts,
        (c.cancel_ts - s.start_ts)   AS secs_start_to_cancel,
        (s.start_ts  - s.install_ts) AS secs_install_to_start
    FROM android_starts s
    LEFT JOIN android_cancels c USING (orig_txn)
),
combined AS (
    SELECT * FROM ios_joined
    UNION ALL
    SELECT * FROM android_joined
)
SELECT
    platform,
    start_event,
    country,
    COUNT(DISTINCT orig_txn)                                                    AS total_starts,
    COUNT(DISTINCT CASE WHEN secs_start_to_cancel IS NOT NULL THEN orig_txn END) AS ever_cancelled,
    COUNT(DISTINCT CASE WHEN secs_start_to_cancel <= 86400   THEN orig_txn END) AS d0_cancel,   -- ≤24h
    COUNT(DISTINCT CASE WHEN secs_start_to_cancel <= 3600    THEN orig_txn END) AS d0_1h_cancel, -- ≤1h
    COUNT(DISTINCT CASE WHEN secs_install_to_start <= 86400
                         AND secs_start_to_cancel <= 86400
                    THEN orig_txn END)                                           AS d0_sub_and_cancel_sameday
FROM combined
GROUP BY 1, 2, 3
ORDER BY platform, total_starts DESC
"""

print("Fetching D0 cancel data (2026-01-01 onwards, all countries)...")
df = client.query(D0_QUERY).to_dataframe()

df["d0_cancel_rate"]   = (df["d0_cancel"]   / df["total_starts"] * 100).round(1)
df["d0_1h_cancel_rate"] = (df["d0_1h_cancel"] / df["total_starts"] * 100).round(1)
df["ever_cancel_rate"] = (df["ever_cancelled"] / df["total_starts"] * 100).round(1)

# ── A. Overall summary (all countries) ──────────────────────────────────────
print("\n══ D0 CANCEL RATE — ALL COUNTRIES ══")
summary = (df.groupby(["platform", "start_event"])
             .agg(total_starts=("total_starts","sum"),
                  d0_cancel=("d0_cancel","sum"),
                  d0_1h_cancel=("d0_1h_cancel","sum"),
                  ever_cancelled=("ever_cancelled","sum"))
             .reset_index())
summary["d0_cancel_rate_pct"]   = (summary["d0_cancel"]   / summary["total_starts"] * 100).round(1)
summary["d0_1h_cancel_rate_pct"] = (summary["d0_1h_cancel"] / summary["total_starts"] * 100).round(1)
summary["ever_cancel_rate_pct"] = (summary["ever_cancelled"] / summary["total_starts"] * 100).round(1)
print(summary[["platform","start_event","total_starts",
               "d0_1h_cancel_rate_pct","d0_cancel_rate_pct","ever_cancel_rate_pct"]].to_string(index=False))

# ── B. US only ───────────────────────────────────────────────────────────────
print("\n══ D0 CANCEL RATE — US ONLY ══")
us = df[df["country"] == "us"].groupby(["platform","start_event"]).agg(
    total_starts=("total_starts","sum"),
    d0_cancel=("d0_cancel","sum"),
    d0_1h_cancel=("d0_1h_cancel","sum"),
    ever_cancelled=("ever_cancelled","sum"),
).reset_index()
us["d0_cancel_rate_pct"]    = (us["d0_cancel"]    / us["total_starts"] * 100).round(1)
us["d0_1h_cancel_rate_pct"] = (us["d0_1h_cancel"] / us["total_starts"] * 100).round(1)
us["ever_cancel_rate_pct"]  = (us["ever_cancelled"] / us["total_starts"] * 100).round(1)
print(us[["platform","start_event","total_starts",
          "d0_1h_cancel_rate_pct","d0_cancel_rate_pct","ever_cancel_rate_pct"]].to_string(index=False))

# ── C. Top 10 countries by D0 cancel difference ─────────────────────────────
print("\n══ D0 CANCEL RATE — TOP COUNTRIES (pivot iOS vs Android) ══")
top_countries = (df.groupby("country")["total_starts"].sum()
                   .nlargest(15).index.tolist())
df_top = df[df["country"].isin(top_countries)].copy()
pivot = (df_top.groupby(["country","platform"])
               .agg(total_starts=("total_starts","sum"),
                    d0_cancel=("d0_cancel","sum"))
               .reset_index())
pivot["d0_rate"] = (pivot["d0_cancel"] / pivot["total_starts"] * 100).round(1)
pivot_wide = pivot.pivot_table(index="country", columns="platform",
                               values=["total_starts","d0_rate"]).reset_index()
pivot_wide.columns = ["_".join(c).strip("_") for c in pivot_wide.columns]
pivot_wide["gap"] = (pivot_wide.get("d0_rate_iOS", 0) - pivot_wide.get("d0_rate_Android", 0)).round(1)
print(pivot_wide.sort_values("gap", ascending=False).to_string(index=False))

# ── D. Chart: D0 cancel rate by start_event type ────────────────────────────
fig = go.Figure()
COLORS = {"iOS": "#E74C3C", "Android": "#2980B9"}

for platform in ["iOS", "Android"]:
    sub = summary[summary["platform"] == platform].sort_values("total_starts", ascending=False)
    fig.add_trace(go.Bar(
        name=platform,
        x=sub["start_event"],
        y=sub["d0_cancel_rate_pct"],
        text=sub.apply(lambda r: f"{r['d0_cancel_rate_pct']}%<br>n={r['total_starts']:,}", axis=1),
        textposition="outside",
        marker_color=COLORS[platform],
    ))

fig.update_layout(
    title="D0 Cancel Rate theo loại subscription start event (≤24h sau khi subscribe)",
    barmode="group",
    paper_bgcolor="#ECF0F1", plot_bgcolor="#ECF0F1",
    font=dict(color="#2C3E50"),
    yaxis=dict(title="D0 Cancel Rate (%)", ticksuffix="%"),
    height=500,
    legend=dict(orientation="h", y=1.05),
)
out = r"c:\Users\admin\Desktop\analytics-ikame\20260623_android-ios-comparison\verify-cancel-android-vs-ios\data\outputs\d0_cancel_rate.html"
fig.write_html(out)
print(f"\nChart saved → {out}")
