import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
import pandas as pd

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json"
client = bigquery.Client(project="team-begamob")

# ── Dữ liệu đã có từ query trước (hardcode để tránh query lại) ───────────────
# ALL COUNTRIES
data_all = {
    "platform":     ["Android","Android","Android","iOS","iOS"],
    "start_event":  ["activation","discounted_offer","trial_started","activation","trial_started"],
    "total_starts": [974,  1105, 3753, 75332, 8387],
    "d0_cancel":    [23.0, 16.2, 19.1, 41.3,  51.6],
    "d0_1h_cancel": [17.1, 12.1, 13.5, 30.2,  38.6],
    "ever_cancel":  [59.0, 20.7, 44.9, 77.4,  74.6],
}
# US ONLY
data_us = {
    "platform":     ["Android","Android","Android","iOS","iOS"],
    "start_event":  ["activation","discounted_offer","trial_started","activation","trial_started"],
    "total_starts": [464,  91,  1199, 44191, 7062],
    "d0_cancel":    [27.8, 28.6, 26.0, 36.4, 51.0],
    "ever_cancel":  [74.6, 36.3, 66.2, 74.6, 73.5],
}

df_all = pd.DataFrame(data_all)
df_us  = pd.DataFrame(data_us)

# Label ngắn gọn
label_map = {"activation":"activation","discounted_offer":"discounted\noffer","trial_started":"trial\nstarted"}
df_all["label"] = df_all["start_event"].map(label_map)
df_us["label"]  = df_us["start_event"].map(label_map)

C_AND = "#2980B9"
C_IOS = "#E74C3C"

fig = make_subplots(
    rows=1, cols=3,
    subplot_titles=[
        "D0 Cancel Rate — All Countries",
        "D0 Cancel Rate — US Only",
        "Ever Cancel Rate — All Countries",
    ],
    horizontal_spacing=0.08,
)

# helper
def add_bars(fig, df, y_col, row, col, showlegend=False):
    for platform, color in [("Android", C_AND), ("iOS", C_IOS)]:
        sub = df[df["platform"] == platform]
        fig.add_trace(go.Bar(
            name=platform,
            x=sub["label"],
            y=sub[y_col],
            text=[f"{v:.0f}%<br><span style='font-size:10px'>n={n:,}</span>"
                  for v, n in zip(sub[y_col], sub["total_starts"])],
            textposition="outside",
            marker_color=color,
            showlegend=showlegend,
        ), row=row, col=col)

add_bars(fig, df_all, "d0_cancel",  1, 1, showlegend=True)
add_bars(fig, df_us,  "d0_cancel",  1, 2)
add_bars(fig, df_all, "ever_cancel",1, 3)

fig.update_layout(
    title=dict(
        text="Android vs iOS — D0 Cancel Rate & Ever Cancel Rate (Jan–Jun 2026)",
        font=dict(size=16, color="#2C3E50"),
    ),
    barmode="group",
    paper_bgcolor="#ECF0F1",
    plot_bgcolor="#ECF0F1",
    font=dict(color="#2C3E50"),
    height=520,
    legend=dict(orientation="h", y=1.08, x=0.4),
    margin=dict(t=100, b=80),
)
for i in range(1, 4):
    fig.update_yaxes(title_text="%" if i == 1 else "", ticksuffix="%", range=[0, 90], row=1, col=i)

# Annotation gap US
gap_act  = 36.4 - 27.8
gap_trial = 51.0 - 26.0
fig.add_annotation(
    x=1.5, y=85, xref="x2", yref="y2",
    text=f"Gap activation: -{gap_act:.1f}pp<br>Gap trial: -{gap_trial:.1f}pp",
    showarrow=False, bgcolor="#F39C12", font=dict(color="white", size=11),
    borderpad=4,
)

out = r"c:\Users\admin\Desktop\analytics-ikame\20260623_android-ios-comparison\verify-cancel-android-vs-ios\data\outputs\d0_summary.html"
fig.write_html(out)
print(f"Chart saved → {out}")

# ── In bảng summary gọn ─────────────────────────────────────────────────────
print("\n── SUMMARY TABLE (US) ──")
print(f"{'Metric':<40} {'Android':>10} {'iOS':>10} {'Gap (A-I)':>10}")
print("-" * 72)
rows = [
    ("D0 cancel — activation",    27.8, 36.4),
    ("D0 cancel — trial_started", 26.0, 51.0),
    ("D0 cancel — disc.offer/n/a",28.6, None),
    ("Ever cancel — activation",  74.6, 74.6),
    ("Ever cancel — trial",       66.2, 73.5),
    ("Ever cancel — disc.offer",  36.3, None),
]
for label, a, i in rows:
    gap_str = f"{a - i:+.1f}pp" if i is not None else "—"
    i_str   = f"{i:.1f}%" if i is not None else "—"
    print(f"  {label:<38} {a:>9.1f}% {i_str:>10} {gap_str:>10}")
