import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2.credentials import Credentials
from google.cloud import bigquery
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CRED_PATH = r"c:\Users\admin\Desktop\analytics-ikame\20260623_ios_face_scanner\scan-vs-purchase-analysis\gcloud_credentials.json"
PROJECT   = "team-begamob"
TABLE     = "`ikame-apps-dev.tracking_transaction_providers.transaction-providers`"

with open(CRED_PATH) as f:
    c = json.load(f)

creds = Credentials(
    token=c.get("access_token"), refresh_token=c.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=c.get("client_id"), client_secret=c.get("client_secret"),
)
client = bigquery.Client(project=PROJECT, credentials=creds)

# ── Fetch data ─────────────────────────────────────────────────────────────────
q = f"""
SELECT
  DATE(createdAt)            AS date,
  transactionType,
  payment_gateway,
  plan_name,
  COUNT(*)                   AS transactions,
  COUNT(DISTINCT userId)     AS unique_users,
  ROUND(SUM(amount_real), 2) AS revenue
FROM {TABLE}
GROUP BY 1,2,3,4
ORDER BY 1,2
"""
df = client.query(q).to_dataframe()
df["date"] = pd.to_datetime(df["date"])

COLORS = {
    "first_purchase": "#27AE60",
    "cancel"        : "#E74C3C",
    "past_due"      : "#F39C12",
}
GW_COLORS = {"Stripe": "#2980B9", "PayPal": "#2C3E50"}
PLAN_COLORS = {
    "1-WEEK PLAN"         : "#2C3E50",
    "4-WEEK PLAN"         : "#2980B9",
    "YEARLY PLAN"         : "#27AE60",
    "Onetime GLP Plan"    : "#F39C12",
    "Onetime GLP Plan sale": "#E74C3C",
    "Calories_webfunnel"  : "#8E44AD",
    "test product"        : "#95A5A6",
}

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=[
        "Daily Revenue by TransactionType",
        "Daily Transactions by TransactionType",
        "Revenue by Payment Gateway (first_purchase only)",
        "Revenue by Plan (first_purchase only)",
        "Unique Users per Day",
        "Revenue Share by Plan (first_purchase)",
    ],
    specs=[
        [{"type": "xy"}, {"type": "xy"}],
        [{"type": "xy"}, {"type": "xy"}],
        [{"type": "xy"}, {"type": "domain"}],
    ],
    vertical_spacing=0.12,
    horizontal_spacing=0.10,
)

dates = sorted(df["date"].unique())

# ── Row 1 left: Revenue by transactionType ────────────────────────────────────
for tt, color in COLORS.items():
    sub = df[df["transactionType"] == tt].groupby("date")["revenue"].sum().reindex(dates, fill_value=0)
    fig.add_trace(go.Bar(
        x=dates, y=sub.values, name=tt,
        marker_color=color, legendgroup=tt,
    ), row=1, col=1)

# ── Row 1 right: Transactions by transactionType ──────────────────────────────
for tt, color in COLORS.items():
    sub = df[df["transactionType"] == tt].groupby("date")["transactions"].sum().reindex(dates, fill_value=0)
    fig.add_trace(go.Bar(
        x=dates, y=sub.values, name=tt,
        marker_color=color, legendgroup=tt, showlegend=False,
    ), row=1, col=2)

# ── Row 2 left: Revenue by payment gateway (first_purchase only) ──────────────
fp = df[df["transactionType"] == "first_purchase"]
for gw, color in GW_COLORS.items():
    sub = fp[fp["payment_gateway"] == gw].groupby("date")["revenue"].sum().reindex(dates, fill_value=0)
    fig.add_trace(go.Bar(
        x=dates, y=sub.values, name=gw,
        marker_color=color, legendgroup=gw,
    ), row=2, col=1)

# ── Row 2 right: Revenue by plan (first_purchase only) ───────────────────────
for plan, color in PLAN_COLORS.items():
    sub = fp[fp["plan_name"] == plan].groupby("date")["revenue"].sum().reindex(dates, fill_value=0)
    if sub.sum() == 0:
        continue
    fig.add_trace(go.Bar(
        x=dates, y=sub.values, name=plan,
        marker_color=color, legendgroup=plan,
    ), row=2, col=2)

# ── Row 3 left: Unique users per day ─────────────────────────────────────────
for tt, color in COLORS.items():
    sub = df[df["transactionType"] == tt].groupby("date")["unique_users"].sum().reindex(dates, fill_value=0)
    fig.add_trace(go.Bar(
        x=dates, y=sub.values, name=tt,
        marker_color=color, legendgroup=tt, showlegend=False,
    ), row=3, col=1)

# ── Row 3 right: Pie - revenue share by plan (first_purchase, all days) ──────
plan_rev = fp.groupby("plan_name")["revenue"].sum().sort_values(ascending=False)
fig.add_trace(go.Pie(
    labels=plan_rev.index.tolist(),
    values=plan_rev.values.tolist(),
    marker_colors=[PLAN_COLORS.get(p, "#95A5A6") for p in plan_rev.index],
    hole=0.4,
    showlegend=True,
    name="",
), row=3, col=2)

# ── Layout ────────────────────────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text="Transaction Providers — Daily Revenue Dashboard<br><sup>dsblack.semantra.cloud | provider: web2wave | 2026-06-22 → 2026-06-23</sup>",
        font=dict(size=18, color="#2C3E50"),
    ),
    barmode="stack",
    paper_bgcolor="#ECF0F1",
    plot_bgcolor="#ECF0F1",
    font=dict(color="#2C3E50", size=12),
    legend=dict(bgcolor="rgba(255,255,255,0.7)", bordercolor="#BDC3C7", borderwidth=1),
    height=900,
)
fig.update_xaxes(tickformat="%b %d", tickangle=-30)

# Annotate daily total on row1 left
daily_total = df[df["transactionType"]=="first_purchase"].groupby("date")["revenue"].sum()
for date, rev in daily_total.items():
    fig.add_annotation(
        x=date, y=rev + 30, text=f"<b>${rev:,.0f}</b>",
        showarrow=False, font=dict(size=11, color="#27AE60"),
        row=1, col=1,
    )

OUT = r"c:\Users\admin\Desktop\analytics-ikame\20260624_wfn_transaction-providers\transaction-providers\data\outputs\revenue_daily.html"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.write_html(OUT)
print(f"Saved: {OUT}")
