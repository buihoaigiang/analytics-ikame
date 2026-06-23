"""So sanh funnel 3.3.5 (intro6) vs 3.3.7 (intro7) - back-to-back, giu nguyen ten man moi version."""
import os
from pathlib import Path
from google.cloud import bigquery
import plotly.graph_objects as go
from plotly.subplots import make_subplots

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\admin\Desktop\20260610\gcloud_credentials.json'
client = bigquery.Client(project='team-begamob')

BG, TEXT = "#ECF0F1", "#2C3E50"
SEVERE = 40.0
VARIANTS = {"membership_benefits", "subscribe5_2"}
NONE_LABEL = "-- (khong co)"

DARK, LIGHT = (44, 62, 80), (174, 182, 191)
def shade(i, n):
    t = i / max(n - 1, 1)
    c = [int(DARK[k] + (LIGHT[k] - DARK[k]) * t) for k in range(3)]
    return f"rgb({c[0]},{c[1]},{c[2]})"

# (screen_3.3.5, screen_3.3.7) -- align theo nhom chuc nang, thu tu top->down
ROWS = [
    ("splash", "splash"),
    ("sign_in_onboarding", "sign_in_onboarding"),
    ("intro6_heart_measure", "intro7_heart_measure"),
    (None, "intro7_learn_more"),
    (None, "intro7_track_stress"),
    ("intro6_heart_report", None),
    ("intro6_blood_pressure", "intro7_blood_pressure"),
    (None, "intro7_blood_sugar"),
    (None, "intro7_check_apple_watch"),
    ("intro6_analyzing", "intro7_analyzing"),
    ("intro6_select_gender", "intro7_select_gender"),
    ("intro6_select_age", "intro7_select_age"),
    ("intro6_select_height", "intro7_select_height"),
    ("intro6_select_weight", "intro7_select_weight"),
    ("intro6_question_health_issue", "intro7_question_health_issue"),
    ("intro6_final_processing", "intro7_final_processing"),
    ("subscribe5", "subscribe5_new"),
    ("home", "home"),
    ("measure", "measure"),
]
N = len(ROWS)
VCOL = {'3.3.5': 0, '3.3.7': 1}

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
stats = {}
for r in client.query(QUERY).result():
    stats[(r.version, r.screen_from)] = (r.pct, r.users)

def drop_chain(version):
    chain = [row[VCOL[version]] for row in ROWS
             if row[VCOL[version]] and row[VCOL[version]] not in VARIANTS]
    d, prev = {}, None
    for scr in chain:
        if (version, scr) in stats:
            pct = stats[(version, scr)][0]
            if prev is not None:
                d[scr] = (prev - pct) / prev * 100
            prev = pct
    return d

DROP = {'3.3.5': drop_chain('3.3.5'), '3.3.7': drop_chain('3.3.7')}

def bar_text(version, scr):
    pct, users = stats[(version, scr)]
    t = f"{pct:.1f}% ({users:,})"
    if scr in DROP[version]:
        t += f"  ▼{DROP[version][scr]:.1f}%"
    return t

# Thang mau xanh -> vang -> do theo do lon (0=xanh tot, 1=do canh bao)
def gyr(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        u = t / 0.5
        c = [int(39 + (241 - 39) * u), int(174 + (196 - 174) * u), int(96 + (15 - 96) * u)]
    else:
        u = (t - 0.5) / 0.5
        c = [int(241 + (231 - 241) * u), int(196 + (76 - 196) * u), int(15 + (60 - 15) * u)]
    return f"rgb({c[0]},{c[1]},{c[2]})"

# y position: row 0 (splash) o TOP -> ypos cao nhat
def ypos(i):
    return N - 1 - i

SUBT = {'3.3.5': "3.3.5 - intro6  (08/05/2026 - 24/05/2026)",
        '3.3.7': "3.3.7 - intro7  (25/05/2026 - 10/06/2026)"}

# (A) Delta tich luy = pct(3.3.5) - pct(3.3.7), chi hang co ca 2 version
deltas, maxabs = {}, 0.0
for idx, row in enumerate(ROWS):
    s5, s7 = row
    if s5 and s7 and ('3.3.5', s5) in stats and ('3.3.7', s7) in stats:
        d = stats[('3.3.5', s5)][0] - stats[('3.3.7', s7)][0]
        deltas[idx] = d
        maxabs = max(maxabs, abs(d))

# (B) Delta vs previous step (pp) = % buoc truoc - % buoc sau, theo chuoi rieng moi version
def step_drop_pp(version):
    res, prev = {}, None
    for idx, row in enumerate(ROWS):
        scr = row[VCOL[version]]
        if scr and scr not in VARIANTS and (version, scr) in stats:
            pct = stats[(version, scr)][0]
            if prev is not None:
                res[idx] = prev - pct
            prev = pct
    return res

STEP = {'3.3.5': step_drop_pp('3.3.5'), '3.3.7': step_drop_pp('3.3.7')}
# (C) Delta-delta = Delta step 3.3.5 - Delta step 3.3.7 (chi hang co ca 2)
dd = {idx: STEP['3.3.5'][idx] - STEP['3.3.7'][idx]
      for idx in STEP['3.3.5'] if idx in STEP['3.3.7']}
maxabs_dd = max((abs(v) for v in dd.values()), default=0.0)

fig = make_subplots(rows=1, cols=3)
# domain thu cong: khe GIUA (col1-col2) hep, khe col2-col3 rong cho nhan 3.3.7
DOM = {1: [0.00, 0.36], 2: [0.375, 0.735], 3: [0.82, 1.0]}

for ci, version in enumerate(['3.3.5', '3.3.7'], start=1):
    xs, ys, txt, cd, colors, tickvals, ticktext = [], [], [], [], [], [], []
    for idx, row in enumerate(ROWS):
        scr = row[VCOL[version]]
        tickvals.append(ypos(idx))
        ticktext.append(scr if scr else NONE_LABEL)
        if scr and (version, scr) in stats:
            xs.append(stats[(version, scr)][0]); ys.append(ypos(idx))
            txt.append(bar_text(version, scr)); cd.append(stats[(version, scr)][1])
            colors.append(shade(idx, N))
    fig.add_trace(go.Bar(
        x=xs, y=ys, orientation='h', marker_color=colors, showlegend=False,
        text=txt, textposition='outside', textfont=dict(size=9, color=TEXT),
        customdata=cd, cliponaxis=False,
        hovertemplate="%{text}<extra></extra>",
    ), row=1, col=ci)
    side = 'left' if ci == 1 else 'right'
    fig.update_yaxes(tickvals=tickvals, ticktext=ticktext, side=side,
                     range=[-0.6, N - 0.4], tickfont=dict(size=10, color=TEXT),
                     showgrid=False, row=1, col=ci)
    # trai: 0 o GIUA (ben phai), bar moc ra TRAI -> dao truc x
    xr = [150, 0] if ci == 1 else [0, 150]
    fig.update_xaxes(range=xr, domain=DOM[ci], title_text="% distinct user_pseudo_id",
                     gridcolor="#D5D8DC", griddash="dash", zeroline=False, row=1, col=ci)

# Title 2 luong (dat thu cong theo domain)
for ci, version in [(1, '3.3.5'), (2, '3.3.7')]:
    fig.add_annotation(xref="paper", yref="paper", x=sum(DOM[ci]) / 2, y=1.0,
                       text=SUBT[version], showarrow=False, xanchor="center",
                       yanchor="bottom", font=dict(size=13, color=TEXT))

# Cot 3: bang chi so. 2 cot: Delta tich luy | Dstep (3.3.5 - 3.3.7) & DD
fig.update_xaxes(visible=False, range=[0, 1], domain=DOM[3], row=1, col=3)
fig.update_yaxes(visible=False, range=[-0.6, N - 0.4], row=1, col=3)
CX = {'cum': 0.20, 'dstep': 0.68}

def fmt_anno(x, idx, text, val, mx, size=9):
    t = abs(val) / mx if mx else 0
    fc = "white" if t > 0.7 else TEXT
    fig.add_annotation(xref="x3", yref="y3", x=x, y=ypos(idx), text=text, showarrow=False,
                       xanchor="center", bgcolor=gyr(t), borderpad=4, font=dict(size=size, color=fc))

def plain_anno(x, idx, text, size=9):  # khong to mau (dung cho doan sau subscribe)
    fig.add_annotation(xref="x3", yref="y3", x=x, y=ypos(idx), text=text, showarrow=False,
                       xanchor="center", font=dict(size=size, color=TEXT))

# index man subscribe -> conditional formatting chi tinh toi het subscribe
SUB_IDX = next(i for i, row in enumerate(ROWS) if row[0] == 'subscribe5')
mx_cum = max((abs(d) for i, d in deltas.items() if i <= SUB_IDX), default=0.0)
mx_dd = max((abs(v) for i, v in dd.items() if i <= SUB_IDX), default=0.0)

# headers
fig.add_annotation(xref="x3", yref="paper", x=CX['cum'], y=1.005, text="vs %remain<br>(3.3.5 - 3.3.7)",
                   showarrow=False, xanchor="center", yanchor="bottom", font=dict(size=9, color=TEXT))
fig.add_annotation(xref="x3", yref="paper", x=CX['dstep'], y=1.005, text="vs %drop vs prev step<br>(3.3.5 - 3.3.7)",
                   showarrow=False, xanchor="center", yanchor="bottom", font=dict(size=9, color=TEXT))

# cot vs %remain (to mau toi het subscribe; sau subscribe de trang)
for idx, d in deltas.items():
    if idx <= SUB_IDX:
        fmt_anno(CX['cum'], idx, f"{d:+.1f}", d, mx_cum)
    else:
        plain_anno(CX['cum'], idx, f"{d:+.1f}")
# cot vs %drop vs prev step gop: chi hien khi CA 2 luong deu co (idx in dd)
for idx in dd:
    s5 = f"{STEP['3.3.5'][idx]:.1f}"
    s7 = f"{STEP['3.3.7'][idx]:.1f}"
    text = f"({s5} - {s7}) {dd[idx]:+.1f}"
    if idx <= SUB_IDX:
        fmt_anno(CX['dstep'], idx, text, dd[idx], mx_dd, size=8)
    else:
        plain_anno(CX['dstep'], idx, text, size=8)

# Duong gach ngang phan tach 5 nhom chuc nang (ke ngang qua toan bo chart)
# bien giua cac nhom = sau row: sign_in(1) | check_apple_watch(8) | final_processing(15) | subscribe(16)
for b in [1, 8, 15, 16]:
    yb = ypos(b) - 0.5
    fig.add_shape(type="line", xref="paper", yref="y", x0=0, x1=1, y0=yb, y1=yb,
                  line=dict(color="#F39C12", width=1.5, dash="dot"), layer="above")

fig.update_layout(
    title=dict(text="So sanh Funnel Splash -> Measure (dau tien) | 3.3.5 vs 3.3.7 | Session 1 | FacebookW2A | US"
                    "<br><sub>▼ = %drop so voi buoc lien truoc cung version</sub>",
               x=0.5, font=dict(size=15, color=TEXT)),
    paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT, size=11),
    height=900, width=1700, margin=dict(l=165, r=20, t=95, b=50),
    bargap=0.22,
)

out = Path(r'C:\Users\admin\Desktop\20260610\funnel_compare_335_337.html')
fig.write_html(out)
print("HTML:", out)
