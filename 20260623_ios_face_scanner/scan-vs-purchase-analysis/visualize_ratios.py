import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "outputs", "facescan_purchase_install_ratios.csv")
df = pd.read_csv(CSV_PATH, parse_dates=["event_date"])
df["event_date_str"] = df["event_date"].dt.strftime("%m/%d")

PALETTE = ["#2C3E50", "#E74C3C", "#2980B9", "#27AE60", "#F39C12"]
BG = "#ECF0F1"
TEXT = "#2C3E50"

fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=("Users theo ngay (UTC+7)", "Ti le % theo ngay (UTC+7)"),
    vertical_spacing=0.18,
)

# Row 1: user counts
fig.add_trace(go.Bar(
    x=df["event_date_str"], y=df["users_install"],
    name="Install (first_open)", marker_color=PALETTE[0],
), row=1, col=1)
fig.add_trace(go.Bar(
    x=df["event_date_str"], y=df["users_purchase"],
    name="Purchase", marker_color=PALETTE[1],
), row=1, col=1)
fig.add_trace(go.Bar(
    x=df["event_date_str"], y=df["users_facescan"],
    name="FaceScan (ft_face_scan)", marker_color=PALETTE[2],
), row=1, col=1)

# Row 2: ratios
fig.add_trace(go.Scatter(
    x=df["event_date_str"], y=df["pct_facescan_per_install"],
    name="FaceScan/Install %", mode="lines+markers",
    marker_color=PALETTE[2], line=dict(width=2),
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=df["event_date_str"], y=df["pct_purchase_per_install"],
    name="Purchase/Install %", mode="lines+markers",
    marker_color=PALETTE[1], line=dict(width=2),
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=df["event_date_str"], y=df["pct_purchase_per_facescan"].fillna(0),
    name="Purchase/FaceScan %", mode="lines+markers",
    marker_color=PALETTE[3], line=dict(width=2, dash="dot"),
), row=2, col=1)

fig.update_layout(
    title=dict(
        text="FaceScan vs Purchase vs Install — iOS Face Scanner",
        font=dict(size=18, color=TEXT),
        x=0.5,
    ),
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(color=TEXT),
    barmode="group",
    legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    height=700,
)
fig.update_xaxes(gridcolor="#BDC3C7", tickangle=-30)
fig.update_yaxes(gridcolor="#BDC3C7")

out_html = os.path.join(os.path.dirname(__file__), "data", "outputs", "facescan_purchase_install_chart.html")
fig.write_html(out_html)
print(f"Chart saved: {out_html}")
