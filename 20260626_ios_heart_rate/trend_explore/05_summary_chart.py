"""
Summary dashboard — periodicity findings in one HTML.
Panel 1: Lag Significance Matrix  (scatter-square grid, categorical axes)
Panel 2: Day-of-Week relative deviation comparison
Panel 3: STL Seasonal overlay for key segments
"""

import os, sys, warnings
os.environ["PYTHONIOENCODING"] = "utf-8"
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, pacf

# ── Config ────────────────────────────────────────────────────────────────────
DATE_FROM     = "2026-01-01"
DATE_TO       = "2026-06-25"
ACF_LAGS      = 30
STL_PERIOD    = 7
MIN_USERS_DAY = 100
MIN_OBS       = 60

BG_COLOR   = "#ECF0F1"
TEXT_COLOR = "#2C3E50"
PALETTE    = ["#2C3E50","#E74C3C","#2980B9","#27AE60","#F39C12",
              "#8E44AD","#16A085","#D35400","#C0392B","#1ABC9C","#7F8C8D"]
DOW_LABELS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# Significance type → color + legend label
SIG_TYPES = {
    "none":      ("#BFC9CA", "Not significant"),
    "acf_only":  ("#2980B9", "ACF only — likely echo of earlier lag"),
    "pacf_only": ("#F39C12", "PACF only — direct effect (ACF masked)"),
    "both":      ("#E74C3C", "ACF + PACF — confirmed real cycle"),
}

BASE_DIR   = os.path.dirname(__file__)
OUT_DIR    = os.path.join(BASE_DIR, "data", "outputs")
full_dates = pd.date_range(DATE_FROM, DATE_TO, freq="D")

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_series(df_dim, seg):
    sub = df_dim[df_dim["segment"] == seg].copy()
    sub["install_date"] = pd.to_datetime(sub["install_date"])
    idx = full_dates
    prs = sub.set_index("install_date")["pay_rate_start"].reindex(idx)
    nu  = sub.set_index("install_date")["new_users"].reindex(idx)
    prs[nu < MIN_USERS_DAY] = np.nan
    return prs.interpolate(method="time", limit=3)


def detrend_stl(s):
    res = STL(s.fillna(s.median()), period=STL_PERIOD, robust=True).fit()
    return pd.Series(res.seasonal + res.resid, index=s.index), res.seasonal


def sig_lags_of(vals, ci):
    upper = ci[:, 1] - vals
    return {lag for lag in range(1, len(vals)) if abs(vals[lag]) > abs(upper[lag])}


# ── Load all series ───────────────────────────────────────────────────────────

series_dict   = {}
seasonal_dict = {}

df_ov = pd.read_csv(os.path.join(OUT_DIR, "overview_trend.csv"),
                    parse_dates=["install_date"])
df_ov = df_ov.set_index("install_date").reindex(full_dates)
df_ov.loc[df_ov["new_users"] < MIN_USERS_DAY, "pay_rate_start"] = np.nan
s_ov  = df_ov["pay_rate_start"].interpolate(method="time", limit=3)
series_dict["overview"] = s_ov

df_tier = pd.read_csv(os.path.join(OUT_DIR, "dim_tier.csv"),
                      parse_dates=["install_date"])
for seg in sorted(df_tier["segment"].dropna().unique()):
    s = load_series(df_tier, seg)
    if s.notna().sum() >= MIN_OBS:
        series_dict[f"tier:{seg}"] = s

df_tsm = pd.read_csv(os.path.join(OUT_DIR, "dim_traffic_source_medium.csv"),
                     parse_dates=["install_date"])
df_tsm["segment"] = df_tsm["segment"].apply(
    lambda x: "FacebookW2A" if str(x).startswith("CPP") else x)
df_tsm = (df_tsm.groupby(["install_date","segment"], as_index=False)
          .agg(new_users=("new_users","sum"),
               purchase_start_amt=("purchase_start_amt","sum")))
df_tsm["pay_rate_start"] = (df_tsm["purchase_start_amt"]
                             / df_tsm["new_users"].replace(0, float("nan")))
for seg in sorted(df_tsm["segment"].dropna().unique()):
    s = load_series(df_tsm, seg)
    if s.notna().sum() >= MIN_OBS:
        series_dict[f"tsm:{seg}"] = s

print(f"Loaded {len(series_dict)} series: {list(series_dict.keys())}")

# ── Compute ACF / PACF ────────────────────────────────────────────────────────

acf_vals_all  = {}
pacf_vals_all = {}
acf_sig_all   = {}
pacf_sig_all  = {}

for label, s in series_dict.items():
    detrended, seasonal = detrend_stl(s)
    seasonal_dict[label] = seasonal
    d = detrended.dropna().fillna(0)
    if len(d) < ACF_LAGS + 5:
        continue
    av, aci = acf(d,  nlags=ACF_LAGS, alpha=0.05)
    pv, pci = pacf(d, nlags=ACF_LAGS, alpha=0.05, method="ywm")
    acf_vals_all[label]  = av
    pacf_vals_all[label] = pv
    acf_sig_all[label]   = sig_lags_of(av, aci)
    pacf_sig_all[label]  = sig_lags_of(pv, pci)

labels = [l for l in series_dict if l in acf_vals_all]
lags   = list(range(1, ACF_LAGS + 1))

# ── Panel 1: Lag Significance Matrix (scatter square grid) ────────────────────
#
# Each cell = one square marker. Categorical y-axis = segment labels.
# 4 traces (one per significance type) → proper legend, no axis confusion.

def sig_type(label, lag):
    a = lag in acf_sig_all.get(label, set())
    p = lag in pacf_sig_all.get(label, set())
    return ("both" if a and p else "acf_only" if a else "pacf_only" if p else "none")

fig1 = go.Figure()

for stype, (color, legend_name) in SIG_TYPES.items():
    xs, ys, hover = [], [], []
    for label in labels:
        av = acf_vals_all.get(label, [0]*(ACF_LAGS+1))
        pv = pacf_vals_all.get(label, [0]*(ACF_LAGS+1))
        for lag in lags:
            if sig_type(label, lag) == stype:
                xs.append(lag)
                ys.append(label)
                hover.append(
                    f"<b>{label}</b><br>"
                    f"Lag {lag}d<br>"
                    f"ACF  = {av[lag]:+.3f}"
                    f"{'  ✓' if lag in acf_sig_all.get(label, set()) else ''}<br>"
                    f"PACF = {pv[lag]:+.3f}"
                    f"{'  ✓' if lag in pacf_sig_all.get(label, set()) else ''}"
                )
    fig1.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers",
        marker=dict(symbol="square", size=15, color=color,
                    line=dict(width=0.5, color="#BFC9CA")),
        name=legend_name,
        hovertext=hover,
        hoverinfo="text",
    ))

# Vertical reference lines at lag 7, 14, 21
for ref_lag in [7, 14, 21]:
    fig1.add_vline(x=ref_lag, line_dash="dot",
                   line_color="#888", line_width=1.2)
    fig1.add_annotation(x=ref_lag, y=len(labels) - 0.3,
                        text=f"{ref_lag}d", showarrow=False,
                        font=dict(size=10, color="#555"),
                        yanchor="bottom")

fig1.update_layout(
    title=dict(
        text="<b>Lag Significance Matrix — ACF vs PACF</b><br>"
             "<sup>Hover for ACF/PACF values. "
             "Red = confirmed real cycle | Blue = ACF-only echo | "
             "Orange = PACF found direct effect | Gray = not significant</sup>",
        font=dict(size=14, color=TEXT_COLOR),
    ),
    paper_bgcolor=BG_COLOR, plot_bgcolor="#FDFEFE",
    font=dict(color=TEXT_COLOR, size=11),
    xaxis=dict(
        title="Lag (days)",
        tickmode="array",
        tickvals=lags,
        ticktext=[str(l) if l % 7 == 0 or l == 1 else "" for l in lags],
        gridcolor="#E5E8E8", gridwidth=1,
        zeroline=False, range=[0.5, ACF_LAGS + 0.5],
    ),
    yaxis=dict(
        title="Segment",
        type="category",
        categoryorder="array",
        categoryarray=labels[::-1],   # top-to-bottom order
        gridcolor="#E5E8E8", gridwidth=1,
    ),
    legend=dict(
        orientation="h", x=0, y=-0.18,
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    height=max(400, 42 * len(labels) + 160),
    margin=dict(l=210, r=40, t=110, b=130),
)

# ── Panel 2: DOW relative deviation ──────────────────────────────────────────

fig2 = go.Figure()
for i, (label, s) in enumerate(series_dict.items()):
    df_s = s.dropna().reset_index()
    df_s.columns = ["date", "prs"]
    df_s["dow"] = df_s["date"].dt.dayofweek
    medians = df_s.groupby("dow")["prs"].median()
    overall = df_s["prs"].median()
    rel = (medians / overall - 1) * 100

    is_ov = (label == "overview")
    fig2.add_trace(go.Scatter(
        x=DOW_LABELS,
        y=[rel.get(d, np.nan) for d in range(7)],
        mode="lines+markers",
        name=label,
        line=dict(color=PALETTE[i % len(PALETTE)],
                  width=3 if is_ov else 1.5,
                  dash="solid" if is_ov else "dot"),
        marker=dict(size=8 if is_ov else 5),
    ))

fig2.add_hline(y=0, line_dash="dash", line_color="#888", line_width=1)
fig2.update_layout(
    title=dict(
        text="<b>Day-of-Week Pattern — % Deviation from Segment Median</b><br>"
             "<sup>Normalised to own median → shape comparable across segments. "
             "Peaks on same day = shared weekly driver.</sup>",
        font=dict(size=14, color=TEXT_COLOR),
    ),
    paper_bgcolor=BG_COLOR, plot_bgcolor="#FDFEFE",
    font=dict(color=TEXT_COLOR),
    xaxis=dict(title="Day of Week", gridcolor="#E5E8E8"),
    yaxis=dict(title="% deviation from median", gridcolor="#E5E8E8",
               ticksuffix="%", zeroline=False),
    legend=dict(orientation="v", x=1.01, y=1, bgcolor="rgba(0,0,0,0)",
                font=dict(size=10)),
    height=460, margin=dict(r=230, t=100),
)

# ── Panel 3: STL Seasonal overlay ────────────────────────────────────────────

KEY_SEGS = ["overview", "tier:Tier01", "tier:Tier03",
            "tsm:Appier", "tsm:Organic", "tsm:FacebookW2A"]
key_segs = [k for k in KEY_SEGS if k in seasonal_dict]

fig3 = go.Figure()
for i, label in enumerate(key_segs):
    seas    = seasonal_dict[label]
    med     = series_dict[label].dropna().median()
    seas_pct = seas / (med + 1e-9) * 100
    is_ov   = (label == "overview")
    fig3.add_trace(go.Scatter(
        x=seas_pct.index, y=seas_pct.values,
        mode="lines", name=label,
        line=dict(color=PALETTE[i % len(PALETTE)],
                  width=3 if is_ov else 1.5),
        opacity=0.9 if is_ov else 0.75,
    ))

fig3.add_hline(y=0, line_dash="dash", line_color="#888", line_width=1)
fig3.update_layout(
    title=dict(
        text="<b>STL Seasonal Component Overlay — Key Segments</b><br>"
             "<sup>Y = seasonal component as % of own median. "
             "In-phase = same weekly driver. Diverging = different drivers.</sup>",
        font=dict(size=14, color=TEXT_COLOR),
    ),
    paper_bgcolor=BG_COLOR, plot_bgcolor="#FDFEFE",
    font=dict(color=TEXT_COLOR),
    xaxis=dict(title="Install Date", tickformat="%b %d", gridcolor="#E5E8E8"),
    yaxis=dict(title="Seasonal component (%)", gridcolor="#E5E8E8",
               ticksuffix="%", zeroline=False),
    legend=dict(orientation="v", x=1.01, y=1, bgcolor="rgba(0,0,0,0)",
                font=dict(size=10)),
    height=400, margin=dict(r=200, t=100),
    hovermode="x unified",
)

# ── Assemble HTML ─────────────────────────────────────────────────────────────

def fig_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Periodicity Summary — ios_heart_rate</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body  {{ background:{BG_COLOR}; color:{TEXT_COLOR};
             font-family:sans-serif; padding:24px; max-width:1200px; margin:auto; }}
    h1    {{ font-size:18px; margin-bottom:2px; }}
    .meta {{ font-size:12px; color:#777; margin-bottom:24px; }}
    .sec  {{ margin-bottom:48px; border-top:2px solid #CCD1D1; padding-top:20px; }}
    h2    {{ font-size:14px; font-weight:600; margin-bottom:4px; }}
    .desc {{ font-size:12px; color:#555; margin-bottom:12px; line-height:1.5; }}
    b.r   {{ color:#E74C3C; }} b.b {{ color:#2980B9; }}
    b.o   {{ color:#F39C12; }}
  </style>
</head>
<body>
  <h1>Periodicity Analysis — ios_heart_rate / Pay Rate Start</h1>
  <p class="meta">Jan 1 – Jun 25 2026 &nbsp;|&nbsp; Cohort day 60 &nbsp;|&nbsp;
     data_source = Adjust &nbsp;|&nbsp; View: User Level &nbsp;|&nbsp;
     n = 176 daily obs (aggregate)</p>

  <div class="sec">
    <h2>1. Lag Significance Matrix (ACF vs PACF)</h2>
    <p class="desc">
      Mỗi ô = 1 lag cho 1 segment.&nbsp;
      <b class="r">Đỏ</b> = ACF <i>và</i> PACF đều significant → chu kỳ thật (direct driver).&nbsp;
      <b class="b">Xanh</b> = chỉ ACF significant → có thể là echo của lag nhỏ hơn, không phải driver thật.&nbsp;
      <b class="o">Cam</b> = chỉ PACF → direct effect bị ACF che khuất.&nbsp;
      Hover để xem giá trị cụ thể.
    </p>
    {fig_html(fig1)}
  </div>

  <div class="sec">
    <h2>2. Day-of-Week Pattern (% deviation from segment median)</h2>
    <p class="desc">
      Y-axis = % lệch so với median của chính segment, không phải PRS tuyệt đối
      → shape các segment có thể so sánh với nhau.
      Đường overview (nét liền đậm) = baseline toàn app.
      Segment có đỉnh cùng ngày với overview = cùng driver tuần.
    </p>
    {fig_html(fig2)}
  </div>

  <div class="sec">
    <h2>3. STL Seasonal Component — Key Segments</h2>
    <p class="desc">
      Component seasonal được tách bằng STL (period=7), scale về % median riêng của từng segment.
      Các đường cùng pha (peak/trough cùng thời điểm) = share cùng weekly driver.
      Đường lệch pha hoặc ngược chiều = driver khác biệt.
    </p>
    {fig_html(fig3)}
  </div>
</body>
</html>"""

out_path = os.path.join(OUT_DIR, "periodicity_summary_chart.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Saved -> {out_path}")
