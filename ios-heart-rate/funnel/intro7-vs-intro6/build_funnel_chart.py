"""Funnel splash -> measure dau tien (session 1), % distinct user theo screen_from, 2 version."""
import os
from pathlib import Path
from google.cloud import bigquery
import plotly.graph_objects as go
from plotly.subplots import make_subplots

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\admin\Desktop\20260610\gcloud_credentials.json'
client = bigquery.Client(project='team-begamob')

# Soft Report palette
BG, PRIMARY, ACCENT, TEXT = "#ECF0F1", "#2C3E50", "#E74C3C", "#2C3E50"

QUERY = """
WITH base AS (
  SELECT version, user_pseudo_id, screen_from,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY event_timestamp, flow_row_number, event_row_in_flow) rn
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium='FacebookW2A' AND session_number=1 AND country='United States'
    AND version IN ('3.3.7','3.3.5')
    AND ((version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24'))
),
fm AS (SELECT user_pseudo_id, MIN(rn) first_measure_rn FROM base WHERE screen_from='measure' GROUP BY user_pseudo_id),
trunc AS (
  SELECT b.version, b.user_pseudo_id, b.screen_from
  FROM base b LEFT JOIN fm USING(user_pseudo_id)
  WHERE fm.first_measure_rn IS NULL OR b.rn <= fm.first_measure_rn
),
tot AS (SELECT version, COUNT(DISTINCT user_pseudo_id) total FROM base GROUP BY version)
SELECT t.version, t.screen_from,
  COUNT(DISTINCT t.user_pseudo_id) users,
  ROUND(100*COUNT(DISTINCT t.user_pseudo_id)/MAX(tot.total),2) pct
FROM trunc t JOIN tot ON t.version=tot.version
GROUP BY t.version, t.screen_from
"""

rows = list(client.query(QUERY).result())

# main label moi version (luong chinh) + date range
DATE_RANGE = {'3.3.5': '08/05/2026 - 24/05/2026', '3.3.7': '25/05/2026 - 10/06/2026'}
LABEL = {v: f"{v} - intro{6 if v=='3.3.5' else 7} ({DATE_RANGE[v]})" for v in ('3.3.5', '3.3.7')}
THRESH = 1.0  # chi ve screen co >= 1% user cho gon

data = {'3.3.5': [], '3.3.7': []}
for r in rows:
    if r.pct >= THRESH:
        data[r.version].append((r.screen_from, r.pct, r.users))

fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.22,
                    subplot_titles=[LABEL['3.3.5'], LABEL['3.3.7']])

for i, v in enumerate(['3.3.5', '3.3.7'], start=1):
    d = sorted(data[v], key=lambda x: x[1])  # asc -> splash (cao nhat) len top
    screens = [x[0] for x in d]
    pcts = [x[1] for x in d]
    users = [x[2] for x in d]
    fig.add_trace(go.Bar(
        x=pcts, y=screens, orientation='h',
        marker_color=PRIMARY,
        text=[f"{p:.2f}% ({u:,})" for p, u in zip(pcts, users)], textposition='outside',
        textfont=dict(size=9, color=TEXT),
        customdata=users,
        hovertemplate="%{y}<br>%{x:.2f}% (%{customdata:,} users)<extra></extra>",
        showlegend=False,
    ), row=1, col=i)
    fig.update_xaxes(range=[0, 135], title_text="% distinct user", row=1, col=i)

fig.update_layout(
    title=dict(text="Funnel Splash -> Measure (dau tien) | Session 1 | FacebookW2A | US | 17 ngay",
               x=0.5, font=dict(size=15, color=TEXT)),
    paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT, size=11),
    height=720, width=1250, margin=dict(l=10, r=40, t=90, b=50),
)
fig.update_xaxes(gridcolor="#D5D8DC", griddash="dash", zeroline=False)
fig.update_yaxes(automargin=True)

out_html = Path(r'C:\Users\admin\Desktop\20260610\funnel_to_measure.html')
fig.write_html(out_html)
print("HTML:", out_html)
try:
    out_png = out_html.with_suffix('.png')
    fig.write_image(out_png, scale=2)
    print("PNG:", out_png)
except Exception as e:
    print("PNG skip (can kaleido):", str(e)[:80])
