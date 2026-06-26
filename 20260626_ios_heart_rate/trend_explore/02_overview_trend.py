"""
Overview Metrics trend chart:
  - Bar:  New Users (by install_date)
  - Line: %Pay Rate Start
  - Line: %Pay Rate Actual
Filter: Day Cohort = 60, View at = User Level, platform = ios
"""

import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

import google.auth
from google.cloud import bigquery
import pandas as pd
import plotly.graph_objects as go

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT    = "team-begamob"
DATASET    = "iOS_Heart_Rate_CACHED_Events_03"
DATE_FROM  = "2026-01-01"
DATE_TO    = "2026-06-25"
COHORT_DAY  = 60           # number_day_install filter
VIEW_AT     = "User Level" # "User Level" or "Event Level"
DATA_SOURCE = "Adjust"     # "Adjust" | "Firebase" | None (all sources)

CREDENTIAL_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "gcloud_credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "gcloud_credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "..", "gcloud_credentials.json"),
    r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json",
]
CRED_PATH = next((p for p in CREDENTIAL_CANDIDATES if os.path.exists(p)), None)
if not CRED_PATH:
    sys.exit("gcloud_credentials.json not found.")

# ── BigQuery ──────────────────────────────────────────────────────────────────
creds, _ = google.auth.load_credentials_from_file(CRED_PATH)
client   = bigquery.Client(project=PROJECT, credentials=creds)

# Choose aggregation columns based on View at
if VIEW_AT == "User Level":
    ps_col  = "purchase_start_users"   # Purchase Start Amount
    iap_col = "iap_users"              # IAP Amount
    pa_col  = "sub_pay_actual_users"   # Pay Actual Amount
else:
    ps_col  = "purchase_start_total"
    iap_col = "iap_total"
    pa_col  = "sub_pay_actual_total"

ds_filter_installs = f"AND data_source = '{DATA_SOURCE}'" if DATA_SOURCE else ""
ds_filter_ps       = f"AND data_source = '{DATA_SOURCE}'" if DATA_SOURCE else ""
ds_filter_conv     = f"AND data_source = '{DATA_SOURCE}'" if DATA_SOURCE else ""

QUERY = f"""
WITH installs AS (
  SELECT
    install_date,
    SUM(new_users) AS new_users
  FROM `{PROJECT}.{DATASET}.sdk_iap_installs`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    {ds_filter_installs}
  GROUP BY install_date
),

pay_start AS (
  SELECT
    install_date,
    SUM({ps_col})  AS purchase_start_amt,
    SUM({iap_col}) AS iap_amt
  FROM `{PROJECT}.{DATASET}.sdk_iap_pay_start_cohort_all_product`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    AND number_day_install = {COHORT_DAY}
    {ds_filter_ps}
  GROUP BY install_date
),

conversion AS (
  SELECT
    install_date,
    SUM({pa_col}) AS pay_actual_amt
  FROM `{PROJECT}.{DATASET}.sdk_iap_conversion_cohort_all_product`
  WHERE install_date BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    AND number_day_install = {COHORT_DAY}
    {ds_filter_conv}
  GROUP BY install_date
)

SELECT
  i.install_date,
  i.new_users,
  IFNULL(ps.purchase_start_amt, 0)                         AS purchase_start_amt,
  IFNULL(ps.iap_amt, 0)                                    AS iap_amt,
  IFNULL(c.pay_actual_amt, 0)                              AS pay_actual_amt,

  -- Pay Rate Start = purchase_start / new_users
  SAFE_DIVIDE(IFNULL(ps.purchase_start_amt, 0), i.new_users) AS pay_rate_start,

  -- Pay Rate Actual = (iap_amt + pay_actual_amt) / new_users
  SAFE_DIVIDE(
    IFNULL(ps.iap_amt, 0) + IFNULL(c.pay_actual_amt, 0),
    i.new_users
  )                                                         AS pay_rate_actual

FROM installs i
LEFT JOIN pay_start  ps ON i.install_date = ps.install_date
LEFT JOIN conversion c  ON i.install_date = c.install_date
ORDER BY i.install_date
"""

print("Running query...")
df = client.query(QUERY).to_dataframe()
print(f"Rows returned: {len(df)}")
print(df.tail(5))

# ── Save CSV ──────────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(__file__), "data", "outputs")
os.makedirs(out_dir, exist_ok=True)
csv_path = os.path.join(out_dir, "overview_trend.csv")
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"CSV saved: {csv_path}")

# ── Plotly Chart ───────────────────────────────────────────────────────────────
PALETTE   = ["#2C3E50", "#E74C3C", "#2980B9", "#27AE60", "#F39C12"]
BG_COLOR  = "#ECF0F1"
TEXT_COLOR = "#2C3E50"

fig = go.Figure()

# Bar — New Users (left axis)
fig.add_trace(go.Bar(
    x    = df["install_date"],
    y    = df["new_users"],
    name = "New Users",
    marker_color = "#2980B9",
    opacity      = 0.75,
    yaxis        = "y1",
))

# Line — %Pay Rate Start (right axis)
fig.add_trace(go.Scatter(
    x    = df["install_date"],
    y    = df["pay_rate_start"],
    name = "%Pay Rate Start",
    mode = "lines",
    line = dict(color="#F39C12", width=2),
    yaxis = "y2",
))

# Line — %Pay Rate Actual (right axis)
fig.add_trace(go.Scatter(
    x    = df["install_date"],
    y    = df["pay_rate_actual"],
    name = "%Pay Rate Actual",
    mode = "lines",
    line = dict(color="#27AE60", width=2),
    yaxis = "y2",
))

fig.update_layout(
    title = dict(
        text = f"Overview Metrics — ios_heart_rate<br>"
               f"<sup>Day Cohort: {COHORT_DAY} | View at: {VIEW_AT} | {DATE_FROM} → {DATE_TO}</sup>",
        font = dict(size=16, color=TEXT_COLOR),
    ),
    paper_bgcolor = BG_COLOR,
    plot_bgcolor  = BG_COLOR,
    font          = dict(color=TEXT_COLOR),
    legend        = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),

    xaxis = dict(
        title       = "Install Date",
        showgrid    = False,
        tickformat  = "%b %d",
        tickangle   = -45,
    ),
    yaxis = dict(
        title    = "New Users",
        showgrid = True,
        gridcolor = "#D5DBDB",
    ),
    yaxis2 = dict(
        title    = "Pay Rate",
        overlaying = "y",
        side       = "right",
        showgrid   = False,
        tickformat = ".1%",
        range      = [0, df[["pay_rate_start", "pay_rate_actual"]].max().max() * 1.3 + 0.001],
    ),
    barmode = "overlay",
    hovermode = "x unified",
)

html_path = os.path.join(out_dir, "overview_trend.html")
fig.write_html(html_path)
print(f"Chart saved: {html_path}")
