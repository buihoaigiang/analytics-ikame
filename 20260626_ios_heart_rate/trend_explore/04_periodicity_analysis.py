"""
Periodicity analysis of pay_rate_start.
Reads local CSVs (no BQ). Outputs HTML charts + periodicity_summary.csv.

Methods:
  1. STL Decomposition (period=7)
  2. Day-of-Week Boxplot + Heatmap (week x weekday)
  3. ACF on detrended series (lags 1-30)
  4. FFT Periodogram on detrended series
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
from scipy.signal import periodogram

# ── Config ────────────────────────────────────────────────────────────────────
DATE_FROM = "2026-01-01"
DATE_TO   = "2026-06-25"
STL_PERIOD      = 7
ACF_LAGS        = 30
MIN_USERS_DAY   = 100   # drop day-obs with fewer new_users (too noisy)
MIN_OBS         = 60    # min valid observations per segment to analyze
DIMS = ["tier", "traffic_source_medium"]

BG_COLOR   = "#ECF0F1"
TEXT_COLOR = "#2C3E50"
PALETTE    = ["#2C3E50", "#E74C3C", "#2980B9", "#27AE60", "#F39C12",
              "#8E44AD", "#16A085", "#D35400"]
DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

BASE_DIR = os.path.dirname(__file__)
OUT_DIR  = os.path.join(BASE_DIR, "data", "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

full_dates = pd.date_range(DATE_FROM, DATE_TO, freq="D")
summary_rows = []

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_series(df_dim, seg_val):
    """Return daily pay_rate_start series for one segment, thresholded & interpolated."""
    sub = df_dim[df_dim["segment"] == seg_val].copy()
    sub["install_date"] = pd.to_datetime(sub["install_date"])
    sub = sub.set_index("install_date").reindex(full_dates)
    # Drop days with too few users (noise)
    sub.loc[sub["new_users"] < MIN_USERS_DAY, "pay_rate_start"] = np.nan
    s = sub["pay_rate_start"]
    # Interpolate short gaps (<= 3 days)
    s = s.interpolate(method="time", limit=3)
    return s


def detrend(series, stl_result):
    """Remove trend: seasonal + residual = detrended."""
    return pd.Series(
        stl_result.seasonal + stl_result.resid,
        index=series.index
    )


def save_html(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.write_html(path, include_plotlyjs="cdn")
    return path


def base_layout(title):
    return dict(
        title=dict(text=title, font=dict(size=14, color=TEXT_COLOR)),
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )


# ── Method 1: STL ─────────────────────────────────────────────────────────────

def analyze_stl(series, label, filename_prefix):
    s_clean = series.dropna()
    if len(s_clean) < STL_PERIOD * 2:
        return None
    # Fill remaining NaN with median for STL
    s_filled = series.fillna(series.median())
    result = STL(s_filled, period=STL_PERIOD, robust=True).fit()

    seasonal_strength = (result.seasonal.max() - result.seasonal.min()) / (series.median() + 1e-9)

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        subplot_titles=["Original", "Trend", "Seasonal (period=7)", "Residual"],
        vertical_spacing=0.07,
    )
    idx = result.seasonal.index
    for row, (name, vals, color) in enumerate([
        ("Original",  s_filled,         "#2980B9"),
        ("Trend",     result.trend,     "#E74C3C"),
        ("Seasonal",  result.seasonal,  "#27AE60"),
        ("Residual",  result.resid,     "#F39C12"),
    ], start=1):
        fig.add_trace(go.Scatter(x=idx, y=vals, mode="lines",
                                 line=dict(color=color, width=1.5), name=name,
                                 showlegend=False), row=row, col=1)

    fig.update_layout(**base_layout(f"STL Decomposition — {label}"))
    for i in range(1, 5):
        fig.update_xaxes(showgrid=False, row=i, col=1)
        fig.update_yaxes(gridcolor="#D5DBDB", row=i, col=1)
    fig.update_xaxes(tickformat="%b %d", row=4, col=1)

    path = save_html(fig, f"stl_{filename_prefix}.html")
    print(f"  STL -> {os.path.basename(path)}")
    return seasonal_strength


# ── Method 2: Day-of-Week ─────────────────────────────────────────────────────

def analyze_dow_segment(series, label):
    """Return dow_df for one segment (used in overlay boxplot)."""
    df = series.dropna().reset_index()
    df.columns = ["date", "pay_rate_start"]
    df["dow"] = df["date"].dt.dayofweek  # 0=Mon
    df["dow_label"] = df["dow"].map(lambda x: DOW_LABELS[x])
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["label"] = label
    return df


def save_dow_boxplot_multi(dow_dfs, dim, filename):
    """Overlay boxplots for multiple segments on one chart."""
    fig = go.Figure()
    for i, (seg_label, df) in enumerate(dow_dfs.items()):
        color = PALETTE[i % len(PALETTE)]
        for dow_i, dow_name in enumerate(DOW_LABELS):
            sub = df[df["dow"] == dow_i]["pay_rate_start"]
            fig.add_trace(go.Box(
                y=sub, x=[dow_name] * len(sub),
                name=seg_label, marker_color=color,
                legendgroup=seg_label,
                showlegend=(dow_i == 0),
                boxpoints=False,
            ))
    fig.update_layout(
        **base_layout(f"Pay Rate Start by Day of Week — {dim}"),
        boxmode="group",
        xaxis=dict(title="Day of Week", categoryorder="array",
                   categoryarray=DOW_LABELS),
        yaxis=dict(title="Pay Rate Start", tickformat=".1%", gridcolor="#D5DBDB"),
    )
    path = save_html(fig, filename)
    print(f"  DOW boxplot -> {os.path.basename(path)}")


def save_dow_heatmap(series, label, filename):
    """Heatmap: rows=week, cols=weekday."""
    df = series.dropna().reset_index()
    df.columns = ["date", "pay_rate_start"]
    df["dow"]  = df["date"].dt.dayofweek
    df["week"] = df["date"].dt.strftime("W%W")
    pivot = df.pivot_table(index="week", columns="dow",
                            values="pay_rate_start", aggfunc="mean")
    pivot.columns = [DOW_LABELS[c] for c in pivot.columns]

    fig = go.Figure(go.Heatmap(
        z=pivot.values * 100,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="RdYlGn",
        colorbar=dict(title="PRS %"),
        hovertemplate="Week: %{y}<br>Day: %{x}<br>PRS: %{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **base_layout(f"Pay Rate Start Heatmap (Week x Weekday) — {label}"),
        xaxis=dict(title="Day of Week"),
        yaxis=dict(title="Week", autorange="reversed"),
    )
    path = save_html(fig, filename)
    print(f"  DOW heatmap -> {os.path.basename(path)}")


def dow_amplitude(series):
    """Return (max_day, min_day, amplitude_pct) from median per DOW."""
    df = series.dropna().reset_index()
    df.columns = ["date", "pay_rate_start"]
    df["dow"] = df["date"].dt.dayofweek
    medians = df.groupby("dow")["pay_rate_start"].median()
    overall = series.dropna().median()
    amp = (medians.max() - medians.min()) / (overall + 1e-9)
    return DOW_LABELS[medians.idxmax()], DOW_LABELS[medians.idxmin()], amp


# ── Method 3: ACF ─────────────────────────────────────────────────────────────

def _sig_lags_from(vals, ci, lags):
    """Return list of significant lags where |ACF/PACF| exceeds 95% CI."""
    upper = ci[:, 1] - vals
    return [lag for lag in lags[1:] if abs(vals[lag]) > abs(upper[lag])]


def _draw_acf_panel(fig, row, lags, vals, ci, sig_lags, title):
    """Draw one ACF or PACF bar panel into a subplot row."""
    upper = ci[:, 1] - vals
    lower = ci[:, 0] - vals
    colors = ["#E74C3C" if lag in sig_lags else "#AABBC0" for lag in lags[1:]]

    # Shaded CI band
    fig.add_trace(go.Scatter(
        x=lags[1:] + lags[1:][::-1],
        y=list(upper[1:]) + list(lower[1:])[::-1],
        fill="toself", fillcolor="rgba(41,128,185,0.12)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ), row=row, col=1)

    # Bars
    for lag, val, color in zip(lags[1:], vals[1:], colors):
        fig.add_trace(go.Bar(x=[lag], y=[val], marker_color=color,
                             showlegend=False), row=row, col=1)

    # Annotate significant lags
    for lag in sig_lags:
        fig.add_annotation(
            x=lag, y=vals[lag] + (0.04 if vals[lag] >= 0 else -0.06),
            text=f"{lag}d", showarrow=False,
            font=dict(size=10, color="#E74C3C"), row=row, col=1,
        )

    # Zero line
    fig.add_hline(y=0, line_color="#888", line_width=0.8, row=row, col=1)


def analyze_acf(series_detrended, label, filename):
    """
    Plot ACF + PACF side-by-side in one HTML.
    ACF  : total autocorrelation at lag k (includes indirect effects via lag 1..k-1)
    PACF : direct autocorrelation at lag k after removing intermediary lag effects
           → PACF lag-7 sig = lag-7 is a REAL driver, not an echo of lag-1

    Returns: (acf_lag7_coeff, acf_lag7_sig, acf_sig_lags, most_sig_lag,
              pacf_lag7_sig, pacf_sig_lags)
    """
    s = series_detrended.dropna().fillna(0)
    if len(s) < ACF_LAGS + 5:
        return None, False, [], None, False, []

    lags = list(range(ACF_LAGS + 1))

    # ACF
    acf_vals, acf_ci   = acf(s,  nlags=ACF_LAGS, alpha=0.05)
    acf_sig            = _sig_lags_from(acf_vals, acf_ci, lags)
    acf_most_sig       = (max(acf_sig, key=lambda l: abs(acf_vals[l]))
                          if acf_sig else None)

    # PACF — method='ywm' (Yule-Walker modified) is stable for short series
    pacf_vals, pacf_ci = pacf(s, nlags=ACF_LAGS, alpha=0.05, method="ywm")
    pacf_sig           = _sig_lags_from(pacf_vals, pacf_ci, lags)

    # ── Build 2-row chart ──────────────────────────────────────────────────────
    acf_label  = f"ACF  — sig lags: {acf_sig  if acf_sig  else 'none'}"
    pacf_label = f"PACF — sig lags: {pacf_sig if pacf_sig else 'none'}"

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[acf_label, pacf_label],
        vertical_spacing=0.18,
    )
    _draw_acf_panel(fig, 1, lags, acf_vals,  acf_ci,  acf_sig,  acf_label)
    _draw_acf_panel(fig, 2, lags, pacf_vals, pacf_ci, pacf_sig, pacf_label)

    for row in [1, 2]:
        fig.update_xaxes(title_text="Lag (days)", dtick=7,
                         gridcolor="#D5DBDB", row=row, col=1)
        fig.update_yaxes(title_text="Correlation", gridcolor="#D5DBDB",
                         zeroline=False, row=row, col=1)

    fig.update_layout(
        **base_layout(
            f"ACF & PACF (detrended) — {label}<br>"
            f"<sup>Red bars = significant (95% CI). "
            f"PACF sig at lag k => lag k is a direct cycle driver.</sup>"
        ),
        height=900,
        bargap=0.15,
    )
    path = save_html(fig, filename)
    print(f"  ACF/PACF -> {os.path.basename(path)}"
          f"  ACF_sig={acf_sig}  PACF_sig={pacf_sig}")

    lag7_coeff = round(acf_vals[7], 4) if 7 <= ACF_LAGS else None
    return (lag7_coeff, 7 in acf_sig, acf_sig, acf_most_sig,
            7 in pacf_sig, pacf_sig)


# ── Method 4: FFT ─────────────────────────────────────────────────────────────

def analyze_fft(series_detrended, label, filename):
    s = series_detrended.dropna().fillna(series_detrended.median())
    if len(s) < 14:
        return None
    freqs, power = periodogram(s.values, fs=1.0)
    with np.errstate(divide="ignore"):
        periods = np.where(freqs[1:] > 0, 1.0 / freqs[1:], np.nan)
    power_trimmed = power[1:]

    # Keep periods 2–60 days
    mask = (periods >= 2) & (periods <= 60)
    periods_m  = periods[mask]
    power_m    = power_trimmed[mask]

    # Top 3 peaks
    top3_idx  = np.argsort(power_m)[-3:][::-1]
    dom_period = periods_m[top3_idx[0]] if len(top3_idx) > 0 else None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periods_m, y=power_m,
                             mode="lines", line=dict(color="#2980B9", width=1.5),
                             name="Power", showlegend=False))
    for rank, idx in enumerate(top3_idx):
        fig.add_annotation(
            x=periods_m[idx], y=power_m[idx],
            text=f"{periods_m[idx]:.1f}d",
            showarrow=True, arrowhead=2, arrowcolor="#E74C3C",
            font=dict(color="#E74C3C", size=11),
        )

    # Mark 7-day line
    fig.add_vline(x=7, line_dash="dash", line_color="#27AE60",
                  annotation_text="7d", annotation_position="top right")

    fig.update_layout(
        **base_layout(f"FFT Periodogram (detrended) — {label}"),
        xaxis=dict(title="Period (days)", gridcolor="#D5DBDB"),
        yaxis=dict(title="Power", gridcolor="#D5DBDB"),
    )
    path = save_html(fig, filename)
    print(f"  FFT    -> {os.path.basename(path)}")
    return round(dom_period, 1) if dom_period else None


# ── Run analysis for one series ───────────────────────────────────────────────

def run_all(series, label, prefix):
    print(f"\n[{label}]  n_obs={series.notna().sum()}")
    stl_result = STL(series.fillna(series.median()), period=STL_PERIOD, robust=True).fit()
    detrended  = detrend(series, stl_result)

    seas_strength = analyze_stl(series, label, prefix)
    dow_df        = analyze_dow_segment(series, label)
    save_dow_heatmap(series, label, f"dow_heatmap_{prefix}.html")
    max_day, min_day, dow_amp = dow_amplitude(series)
    acf_lag7, acf7_sig, acf_sig_lags, most_sig_lag, pacf7_sig, pacf_sig_lags = \
        analyze_acf(detrended, label, f"acf_{prefix}.html")
    dom_period = analyze_fft(detrended, label, f"fft_{prefix}.html")

    # Verdict: lag-7 is a CONFIRMED direct cycle if PACF lag-7 is also significant
    lag7_confirmed = acf7_sig and pacf7_sig

    summary_rows.append(dict(
        segment              = label,
        n_obs                = int(series.notna().sum()),
        dominant_period_fft  = dom_period,
        acf_sig_lags         = str(acf_sig_lags)  if acf_sig_lags  else "none",
        pacf_sig_lags        = str(pacf_sig_lags) if pacf_sig_lags else "none",
        most_sig_lag_acf     = most_sig_lag,
        acf_lag7_coeff       = round(acf_lag7, 4) if acf_lag7 is not None else None,
        acf_lag7_sig         = acf7_sig,
        pacf_lag7_sig        = pacf7_sig,
        lag7_confirmed       = lag7_confirmed,
        dow_max_day          = max_day,
        dow_min_day          = min_day,
        dow_amplitude_pct    = round(dow_amp * 100, 2),
        stl_seasonal_strength= round(seas_strength * 100, 2) if seas_strength else None,
    ))
    return dow_df


# ── Main ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("SECTION 1 — Aggregate (overview)")
print("=" * 60)

df_ov = pd.read_csv(os.path.join(OUT_DIR, "overview_trend.csv"),
                    parse_dates=["install_date"])
df_ov = df_ov.set_index("install_date").reindex(full_dates)
df_ov.loc[df_ov["new_users"] < MIN_USERS_DAY, "pay_rate_start"] = np.nan
s_overview = df_ov["pay_rate_start"].interpolate(method="time", limit=3)

dow_overview = run_all(s_overview, "overview", "overview")

print("\n" + "=" * 60)
print("SECTION 2 — Dimensional analysis")
print("=" * 60)

for dim in DIMS:
    csv_path = os.path.join(OUT_DIR, f"dim_{dim}.csv")
    df_dim = pd.read_csv(csv_path, parse_dates=["install_date"])

    # For traffic_source_medium: merge CPP_* into FacebookW2A
    if dim == "traffic_source_medium":
        df_dim["segment"] = df_dim["segment"].apply(
            lambda x: "FacebookW2A" if str(x).startswith("CPP") else x
        )
        # Re-aggregate after remap
        df_dim = (df_dim.groupby(["install_date", "segment"], as_index=False)
                  .agg(new_users=("new_users", "sum"),
                       purchase_start_amt=("purchase_start_amt", "sum")))
        df_dim["pay_rate_start"] = df_dim["purchase_start_amt"] / df_dim["new_users"].replace(0, float("nan"))

    # Qualifying segments
    segments = df_dim["segment"].dropna().unique().tolist()
    print(f"\n--- dim={dim} ({len(segments)} candidates) ---")

    dow_dfs = {}
    for seg in segments:
        s = make_series(df_dim, seg)
        n_valid = int(s.notna().sum())
        if n_valid < MIN_OBS:
            print(f"  SKIP {seg} (n={n_valid} < {MIN_OBS})")
            continue
        prefix   = f"{dim}_{str(seg).replace(' ','_').replace('/','_')}"
        dow_df   = run_all(s, f"{dim}:{seg}", prefix)
        dow_dfs[str(seg)] = dow_df

    if dow_dfs:
        save_dow_boxplot_multi(dow_dfs, dim, f"dow_boxplot_{dim}.html")

# ── Summary CSV ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
df_summary = pd.DataFrame(summary_rows)
summary_path = os.path.join(OUT_DIR, "periodicity_summary.csv")
df_summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
print(f"Summary -> {summary_path}")
print(df_summary[["segment","n_obs",
                   "acf_sig_lags","pacf_sig_lags",
                   "acf_lag7_sig","pacf_lag7_sig","lag7_confirmed",
                   "dow_amplitude_pct","stl_seasonal_strength"]].to_string(index=False))
print("\nDone.")
