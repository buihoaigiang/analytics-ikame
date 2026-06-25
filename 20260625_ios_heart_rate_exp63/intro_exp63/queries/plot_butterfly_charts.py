"""
Vẽ 3 butterfly funnel charts:
  1. Baseline vs FlowIntro14_IAP_New
  2. Baseline vs Rollback (US only)
  3. FlowIntro14_IAP_New vs Rollback

Input : data/outputs/funnel_data.json  (từ query_funnel_us_only.py)
Output: data/outputs/funnel_ab_exp63.html
        data/outputs/funnel_baseline_vs_rollback.html
        data/outputs/funnel_v1_vs_rollback.html
"""
import plotly.graph_objects as go
import json, os

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_FILE = os.path.join(BASE_DIR, 'data', 'outputs', 'funnel_data.json')
OUT_DIR   = os.path.join(BASE_DIR, 'data', 'outputs')

with open(DATA_FILE) as f:
    d = json.load(f)

B   = d['B'];   T_B  = d['T_B']
V1  = d['V1'];  T_V1 = d['T_V1']
RB  = d['RB'];  T_RB = d['T_RB']

# ── Helpers ─────────────────────────────────────────────────────────────────
def calc_drops(pcts):
    drops, prev = [None], None
    for p in pcts[1:]:
        if p is not None and prev is not None:
            drops.append(round(p - prev, 1))
        else:
            drops.append(None)
        if p is not None:
            prev = p
    return drops

def dstr(d):
    if d is None: return ''
    sign = chr(9660) if d < 0 else chr(9650)
    return f' {sign}{abs(d):.1f}pp'

def dtxt(left, right):
    if left is None and right is not None: return f'{right:+.1f}pp*'
    if right is None and left is not None: return '-'
    if left is None or right is None:      return ''
    d = round(right - left, 1)
    return ('+' if d >= 0 else '') + f'{d:.1f}pp'

def dcol(left, right):
    if left is None or right is None: return '#9AAAB8'
    d = right - left
    return '#2D7A4F' if d > 0.5 else ('#B83232' if d < -0.5 else '#9AAAB8')

def build_fig(screens, left_name, right_name, l_color_fn, r_color_fn,
              title, subtitle, delta_label, highlight_bands=None):
    labels = [s[0] for s in screens]
    lp = [s[1] for s in screens]
    rp = [s[2] for s in screens]
    ld = calc_drops(lp)
    rd = calc_drops(rp)

    lr  = labels[::-1]
    lpr = lp[::-1];  rpr = rp[::-1]
    ldr = ld[::-1];  rdr = rd[::-1]

    lx = [-(p if p is not None else 0) for p in lpr]
    rx = [(p  if p is not None else 0) for p in rpr]
    lc = [l_color_fn(n, p) for n, p in zip(lr, lpr)]
    rc = [r_color_fn(n, p) for n, p in zip(lr, rpr)]

    lt = [f'{p:.1f}%{dstr(d)}' if p is not None else '' for p, d in zip(lpr, ldr)]
    rt = [f'{p:.1f}%{dstr(d)}' if p is not None else '' for p, d in zip(rpr, rdr)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=lx, y=lr, orientation='h', name=left_name,
        marker=dict(color=lc, line=dict(width=0)),
        text=lt, textposition='auto',
        textfont=dict(size=9, color='white', family='Arial'),
        customdata=[f'{p:.1f}%' if p is not None else '-' for p in lpr],
        hovertemplate='<b>%{y}</b><br>' + left_name.split(' (')[0] + ': <b>%{customdata}</b><extra></extra>',
    ))
    fig.add_trace(go.Bar(
        x=rx, y=lr, orientation='h', name=right_name,
        marker=dict(color=rc, line=dict(width=0)),
        text=rt, textposition='auto',
        textfont=dict(size=9, color='white', family='Arial'),
        customdata=[f'{p:.1f}%' if p is not None else '-' for p in rpr],
        hovertemplate='<b>%{y}</b><br>' + right_name.split(' (')[0] + ': <b>%{customdata}</b><extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=[110]*len(lr), y=lr, mode='text',
        text=[dtxt(l, r) for l, r in zip(lpr, rpr)],
        textfont=dict(size=9, color=[dcol(l, r) for l, r in zip(lpr, rpr)], family='Arial'),
        showlegend=False, hoverinfo='skip',
    ))

    shapes = []
    if highlight_bands:
        for start_l, end_l, fill, border in highlight_bands:
            idxs = [i for i, lbl in enumerate(lr) if lbl in (start_l, end_l)]
            if idxs:
                shapes.append(dict(
                    type='rect', layer='below', xref='x', yref='y',
                    x0=-112, x1=116,
                    y0=min(idxs)-0.5, y1=max(idxs)+0.5,
                    fillcolor=fill,
                    line=dict(color=border, width=1.5, dash='dot'),
                ))

    N = len(lr)
    fig.update_layout(
        title=dict(
            text=f'{title}<br><sup>{subtitle}</sup>',
            x=0.5, xanchor='center',
            font=dict(size=14, color='#1A2535', family='Arial'),
        ),
        barmode='overlay',
        xaxis=dict(
            title='% distinct user_pseudo_id (denominator = splash users)',
            range=[-112, 118],
            tickvals=[-100,-75,-50,-25,0,25,50,75,100],
            ticktext=['100%','75%','50%','25%','0','25%','50%','75%','100%'],
            gridcolor='#DDE4EE', showgrid=True,
            zeroline=True, zerolinewidth=2, zerolinecolor='#95A5A6',
            tickfont=dict(size=10, color='#566882'),
        ),
        yaxis=dict(tickfont=dict(size=10.5, color='#1A2535', family='Arial'), automargin=True),
        plot_bgcolor='#F0F4F8', paper_bgcolor='#F0F4F8',
        font=dict(color='#1A2535', family='Arial'),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.01,
            xanchor='center', x=0.46, font=dict(size=11),
            bgcolor='rgba(240,244,248,0.8)', bordercolor='#DDE4EE', borderwidth=1,
        ),
        height=max(780, N*36+200),
        margin=dict(l=290, r=100, t=110, b=65),
        bargap=0.22, shapes=shapes,
        annotations=[
            dict(x=110, y=N-0.3, xref='x', yref='y', text=delta_label,
                 showarrow=False, font=dict(size=9, color='#8FA0B0', family='Arial'), xanchor='center'),
            dict(x=110, y=N-0.85, xref='x', yref='y', text='* 1 side only',
                 showarrow=False, font=dict(size=8, color='#C4720A', family='Arial'), xanchor='center'),
        ],
    )
    return fig

def save(fig, fname):
    path = os.path.join(OUT_DIR, fname)
    fig.write_html(path, include_plotlyjs=True)
    kb = os.path.getsize(path)/1024
    print(f'Saved: {fname}  ({kb:.0f} KB)')

# ── Chart 1: Baseline vs FlowIntro14_IAP_New ─────────────────────────────────
S_AB = [
    ('splash',                              B['splash'],   V1['splash']),
    ('sign_in_onboarding',                  B['sign_in_onboarding'],   V1['sign_in_onboarding']),
    ('intro7_heart_measure',                B['intro7_heart_measure'], V1['intro7_heart_measure']),
    ('intro7_learn_more',                   B['intro7_learn_more'],    V1['intro7_learn_more']),
    ('intro7_track_stress',                 B['intro7_track_stress'],  V1['intro7_track_stress']),
    ('intro7_blood_pressure',               B['intro7_blood_pressure'],V1['intro7_blood_pressure']),
    ('intro7_blood_sugar',                  B['intro7_blood_sugar'],   V1['intro7_blood_sugar']),
    ('intro7_check_apple_watch',            B['intro7_check_apple_watch'], V1['intro7_check_apple_watch']),
    ('intro7_analyzing',                    B['intro7_analyzing'],     V1['intro7_analyzing']),
    # V1 inserts paywall HERE (step 8, after intro7_analyzing)
    ('[V1] subscribe5_new  [step 8]',       None, V1['subscribe5_new']),
    ('intro7_select_gender',                B['intro7_select_gender'], V1['intro7_select_gender']),
    ('intro7_select_age',                   B['intro7_select_age'],    V1['intro7_select_age']),
    ('intro7_select_height',                B['intro7_select_height'], V1['intro7_select_height']),
    ('intro7_select_weight',                B['intro7_select_weight'], V1['intro7_select_weight']),
    ('intro7_question_health_issue',        B['intro7_question_health_issue'], V1['intro7_question_health_issue']),
    ('intro7_final_processing',             B['intro7_final_processing'], V1['intro7_final_processing']),
    # Baseline paywall HERE (step 14)
    ('[Base] subscribe5_new  [step 14]',    B['subscribe5_new'], None),
    ('subscribe5_2',                        B['subscribe5_2'],  V1['subscribe5_2']),
    ('new_home_v2',                         B['new_home_v2'],   V1['new_home_v2']),
    ('measure',                             B['measure'],       V1['measure']),
    ('how_we_take_measurements',            B['how_we_take_measurements'], V1['how_we_take_measurements']),
    ('new_mood_activity',                   B['new_mood_activity'],    V1['new_mood_activity']),
    ('measure_result2',                     B['measure_result2'],      V1['measure_result2']),
]

fig1 = build_fig(
    S_AB,
    left_name  = f'Baseline (n={T_B:,}, exp63)',
    right_name = f'FlowIntro14_IAP_New (n={T_V1:,}, exp63)',
    l_color_fn = lambda n, p: 'rgba(0,0,0,0)' if p is None else '#1B3A57',
    r_color_fn = lambda n, p: 'rgba(0,0,0,0)' if p is None else ('#C4720A' if '[V1]' in n else '#B83232'),
    title      = 'So sanh Funnel: Baseline vs FlowIntro14_IAP_New',
    subtitle   = (f'firebase_exp_63 | Session 1 | country=United States | '
                  f'Baseline n={T_B:,}, V1 n={T_V1:,} | subscribe5_new vi tri khac nhau'),
    delta_label = 'D V1-Base',
    highlight_bands=[
        ('intro7_analyzing', '[V1] subscribe5_new  [step 8]',
         'rgba(196,114,10,0.10)', 'rgba(196,114,10,0.45)'),
    ],
)
save(fig1, 'funnel_ab_exp63.html')

# ── Chart 2: Baseline vs Rollback ────────────────────────────────────────────
S_B_RB = [
    ('splash',                           B['splash'],    RB['splash']),
    ('sign_in_onboarding',               B['sign_in_onboarding'], RB['sign_in_onboarding']),
    ('intro7_heart_measure',             B['intro7_heart_measure'], RB['intro7_heart_measure']),
    ('intro7_learn_more',                B['intro7_learn_more'],   RB['intro7_learn_more']),
    ('intro7_track_stress',              B['intro7_track_stress'], RB['intro7_track_stress']),
    ('intro7_blood_pressure',            B['intro7_blood_pressure'],RB['intro7_blood_pressure']),
    ('intro7_blood_sugar',               B['intro7_blood_sugar'],  RB['intro7_blood_sugar']),
    ('intro7_check_apple_watch',         B['intro7_check_apple_watch'], RB['intro7_check_apple_watch']),
    ('intro7_analyzing',                 B['intro7_analyzing'],    RB['intro7_analyzing']),
    ('intro7_select_gender',             B['intro7_select_gender'],RB['intro7_select_gender']),
    ('intro7_select_age',                B['intro7_select_age'],   RB['intro7_select_age']),
    ('intro7_select_height',             B['intro7_select_height'],RB['intro7_select_height']),
    ('intro7_select_weight',             B['intro7_select_weight'],RB['intro7_select_weight']),
    ('intro7_question_health_issue',     B['intro7_question_health_issue'], RB['intro7_question_health_issue']),
    ('intro7_final_processing',          B['intro7_final_processing'], RB['intro7_final_processing']),
    ('subscribe5_new  [step 15]',        B['subscribe5_new'],      RB['subscribe5_new']),
    ('subscribe5_2',                     B['subscribe5_2'],         RB['subscribe5_2']),
    ('new_home_v2',                      B['new_home_v2'],          RB['new_home_v2']),
    ('measure',                          B['measure'],              RB['measure']),
    ('how_we_take_measurements',         B['how_we_take_measurements'], RB['how_we_take_measurements']),
    ('new_mood_activity',                B['new_mood_activity'],   RB['new_mood_activity']),
    ('measure_result2',                  B['measure_result2'],     RB['measure_result2']),
]

fig2 = build_fig(
    S_B_RB,
    left_name  = f'Baseline (n={T_B:,}, exp63, 18-21/06)',
    right_name = f'Rollback US-only (n={T_RB:,}, >=22/06)',
    l_color_fn = lambda n, p: 'rgba(0,0,0,0)' if p is None else '#1B3A57',
    r_color_fn = lambda n, p: 'rgba(0,0,0,0)' if p is None else '#1A6B45',
    title      = 'Funnel: Baseline vs Rollback (US only)',
    subtitle   = (f'Baseline exp63 (18-21/06, n={T_B:,}) vs Rollback US-only (>=22/06, n={T_RB:,}) | '
                  f'Session 1 | country=United States'),
    delta_label = 'D RB-Base',
)
save(fig2, 'funnel_baseline_vs_rollback.html')

# ── Chart 3: FlowIntro14_IAP_New vs Rollback ─────────────────────────────────
S_V1_RB = [
    ('splash',                                  V1['splash'],  RB['splash']),
    ('sign_in_onboarding',                      V1['sign_in_onboarding'],  RB['sign_in_onboarding']),
    ('intro7_heart_measure',                    V1['intro7_heart_measure'],RB['intro7_heart_measure']),
    ('intro7_learn_more',                       V1['intro7_learn_more'],   RB['intro7_learn_more']),
    ('intro7_track_stress',                     V1['intro7_track_stress'], RB['intro7_track_stress']),
    ('intro7_blood_pressure',                   V1['intro7_blood_pressure'],RB['intro7_blood_pressure']),
    ('intro7_blood_sugar',                      V1['intro7_blood_sugar'],  RB['intro7_blood_sugar']),
    ('intro7_check_apple_watch',                V1['intro7_check_apple_watch'], RB['intro7_check_apple_watch']),
    ('intro7_analyzing',                        V1['intro7_analyzing'],    RB['intro7_analyzing']),
    ('[V1] subscribe5_new  [step 8]',           V1['subscribe5_new'], None),
    ('intro7_select_gender',                    V1['intro7_select_gender'],RB['intro7_select_gender']),
    ('intro7_select_age',                       V1['intro7_select_age'],   RB['intro7_select_age']),
    ('intro7_select_height',                    V1['intro7_select_height'],RB['intro7_select_height']),
    ('intro7_select_weight',                    V1['intro7_select_weight'],RB['intro7_select_weight']),
    ('intro7_question_health_issue',            V1['intro7_question_health_issue'], RB['intro7_question_health_issue']),
    ('intro7_final_processing',                 V1['intro7_final_processing'], RB['intro7_final_processing']),
    ('[RB] subscribe5_new  [step 15]',          None, RB['subscribe5_new']),
    ('subscribe5_2',                            V1['subscribe5_2'],        RB['subscribe5_2']),
    ('new_home_v2',                             V1['new_home_v2'],         RB['new_home_v2']),
    ('measure',                                 V1['measure'],             RB['measure']),
    ('how_we_take_measurements',                V1['how_we_take_measurements'], RB['how_we_take_measurements']),
    ('new_mood_activity',                       V1['new_mood_activity'],   RB['new_mood_activity']),
    ('measure_result2',                         V1['measure_result2'],     RB['measure_result2']),
]

fig3 = build_fig(
    S_V1_RB,
    left_name  = f'FlowIntro14_IAP_New (n={T_V1:,}, exp63, 18-21/06)',
    right_name = f'Rollback US-only (n={T_RB:,}, >=22/06)',
    l_color_fn = lambda n, p: 'rgba(0,0,0,0)' if p is None else ('#C4720A' if '[V1]' in n else '#B83232'),
    r_color_fn = lambda n, p: 'rgba(0,0,0,0)' if p is None else '#1A6B45',
    title      = 'Funnel: FlowIntro14_IAP_New vs Rollback',
    subtitle   = (f'V1 exp63 (18-21/06, n={T_V1:,}) vs Rollback US-only (>=22/06, n={T_RB:,}) | '
                  f'Session 1 | country=United States | V1 paywall step 8 vs RB step 15'),
    delta_label = 'D RB-V1',
    highlight_bands=[
        ('[V1] subscribe5_new  [step 8]', '[V1] subscribe5_new  [step 8]',
         'rgba(196,114,10,0.10)', 'rgba(196,114,10,0.45)'),
    ],
)
save(fig3, 'funnel_v1_vs_rollback.html')

# Summary CVR
print("\n=== 2nd Paywall Reach Rate Summary ===")
b_cvr  = B['subscribe5_2']  / B['subscribe5_new']  * 100
v1_cvr = V1['subscribe5_2'] / V1['subscribe5_new'] * 100
rb_cvr = RB['subscribe5_2'] / RB['subscribe5_new'] * 100
print(f"Baseline       : paywall {B['subscribe5_new']:.1f}%  -> sub5_2 {B['subscribe5_2']:.1f}%  -> ratio {b_cvr:.1f}%")
print(f"FlowIntro14 V1 : paywall {V1['subscribe5_new']:.1f}% -> sub5_2 {V1['subscribe5_2']:.1f}%  -> ratio {v1_cvr:.1f}%")
print(f"Rollback US    : paywall {RB['subscribe5_new']:.1f}%  -> sub5_2 {RB['subscribe5_2']:.1f}%  -> ratio {rb_cvr:.1f}%")
