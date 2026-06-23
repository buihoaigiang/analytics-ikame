"""Funnel 3.3.7 - intro7: 5 nhom mau chuc nang + step-to-step drop + canh bao bottleneck."""
import os
from pathlib import Path
from google.cloud import bigquery
import plotly.graph_objects as go

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\admin\Desktop\20260610\gcloud_credentials.json'
client = bigquery.Client(project='team-begamob')

BG, TEXT = "#ECF0F1", "#2C3E50"
# 5 nhom mau: G1 dark, G2 blue, G3 green, G4 RED (canh bao paywall), G5 orange
GROUP_COLOR = {1: "#2C3E50", 2: "#2980B9", 3: "#27AE60", 4: "#E74C3C", 5: "#F39C12"}
GROUP_NAME = {
    1: "1. Khoi dong & Dang ky",
    2: "2. Gioi thieu & Giao duc",
    3: "3. Phan tich & Khao sat",
    4: "4. Paywall (goi moi tra phi)",
    5: "5. Trai nghiem tinh nang chinh",
}
DATE_RANGE = "25/05/2026 - 10/06/2026"
SEVERE = 40.0  # drop >= 40% => bottleneck

# Thu tu ph;u top->down + nhom + co thuoc main_chain (de tinh drop) khong
FUNNEL = [  # (screen, group, in_main_chain)
    ("splash", 1, True), ("sign_in_onboarding", 1, True),
    ("intro7_heart_measure", 2, True), ("intro7_learn_more", 2, True),
    ("intro7_track_stress", 2, True), ("intro7_blood_pressure", 2, True),
    ("intro7_blood_sugar", 2, True), ("intro7_check_apple_watch", 2, True),
    ("intro7_analyzing", 3, True), ("intro7_select_gender", 3, True),
    ("intro7_select_age", 3, True), ("intro7_select_height", 3, True),
    ("intro7_select_weight", 3, True), ("intro7_question_health_issue", 3, True),
    ("intro7_final_processing", 3, True),
    ("subscribe5_new", 4, True), ("subscribe5_2", 4, False),  # _2 = bien the, bo khoi chuoi drop
    ("home", 5, True), ("measure", 5, True),
]

QUERY = """
WITH base AS (
  SELECT version, user_pseudo_id, screen_from,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY event_timestamp, flow_row_number, event_row_in_flow) rn
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium='FacebookW2A' AND session_number=1 AND country='United States'
    AND version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10'
),
fm AS (SELECT user_pseudo_id, MIN(rn) first_measure_rn FROM base WHERE screen_from='measure' GROUP BY user_pseudo_id),
trunc AS (
  SELECT b.user_pseudo_id, b.screen_from
  FROM base b LEFT JOIN fm USING(user_pseudo_id)
  WHERE fm.first_measure_rn IS NULL OR b.rn <= fm.first_measure_rn
),
tot AS (SELECT COUNT(DISTINCT user_pseudo_id) total FROM base)
SELECT screen_from,
  COUNT(DISTINCT user_pseudo_id) users,
  ROUND(100*COUNT(DISTINCT user_pseudo_id)/MAX((SELECT total FROM tot)),2) pct
FROM trunc GROUP BY screen_from
"""
stats = {r.screen_from: (r.pct, r.users) for r in client.query(QUERY).result()}

# Tinh step-to-step drop tren MAIN CHAIN
drop = {}
prev_pct, prev_scr = None, None
for scr, g, in_main in FUNNEL:
    if scr not in stats:
        continue
    pct, _ = stats[scr]
    if in_main:
        if prev_pct is not None:
            drop[scr] = (prev_pct - pct) / prev_pct * 100
        prev_pct, prev_scr = pct, scr

# Build text + canh bao
def make_text(scr, in_main):
    pct, users = stats[scr]
    t = f"{pct:.1f}% ({users:,})"
    if not in_main:
        return t + "  (bien the)"
    if scr in drop:
        d = drop[scr]
        t += f"   ▼{d:.0f}%"
        if d >= SEVERE:
            t += " ⚠️"
    return t

# Plotly: orientation h => phan tu dau nam DUOI cung. categoryarray dao nguoc de splash len top.
display = [(s, g, im) for (s, g, im) in FUNNEL if s in stats]
cat_order = [s for (s, g, im) in display][::-1]  # bottom->top

fig = go.Figure()
for g in [1, 2, 3, 4, 5]:
    scrs = [s for (s, gg, im) in display if gg == g]
    if not scrs:
        continue
    fig.add_trace(go.Bar(
        x=[stats[s][0] for s in scrs], y=scrs, orientation='h',
        marker_color=GROUP_COLOR[g], name=GROUP_NAME[g],
        text=[make_text(s, im) for (s, gg, im) in display if gg == g],
        textposition='outside', textfont=dict(size=10, color=TEXT),
        customdata=[stats[s][1] for s in scrs],
        hovertemplate="%{y}<br>%{x:.2f}% (%{customdata:,} users)<extra></extra>",
    ))

fig.update_yaxes(categoryorder='array', categoryarray=cat_order, automargin=True)
fig.update_xaxes(range=[0, 145], title_text="% distinct user (tich luy)",
                 gridcolor="#D5D8DC", griddash="dash", zeroline=False)
fig.update_layout(
    title=dict(text=f"Funnel 3.3.7 - intro7 | Splash -> Measure (dau tien) | Session 1 | FacebookW2A | US"
                    f"<br><sub>{DATE_RANGE} (17 ngay) | ▼ = drop so voi buoc lien truoc | ⚠️ = diem nghen (drop >= {SEVERE:.0f}%)</sub>",
               x=0.5, font=dict(size=15, color=TEXT)),
    paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT, size=11),
    height=760, width=1080, margin=dict(l=10, r=40, t=110, b=50),
    legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='center', x=0.5,
                bgcolor='rgba(0,0,0,0)', font=dict(size=9)),
    bargap=0.25,
)

out = Path(r'C:\Users\admin\Desktop\20260610\funnel_337_grouped.html')
fig.write_html(out)
print("HTML:", out)
fig.write_image(out.with_suffix('.png'), scale=2)
print("PNG:", out.with_suffix('.png'))
