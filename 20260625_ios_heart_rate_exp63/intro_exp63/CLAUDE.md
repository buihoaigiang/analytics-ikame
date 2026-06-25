# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Phân tích A/B test `firebase_exp_63` (AB_IAP_Intro14) trên **iOS Heart Rate** app.  
**Kết luận**: Baseline thắng. FlowIntro14_IAP_New đã bị tắt. Analysis hoàn chỉnh tại `data/outputs/analysis_exp63.md`.

## Experiment

| | Baseline (variant=`'0'`) | FlowIntro14_IAP_New (variant=`'1'`) | Rollback |
|--|--|--|--|
| Paywall position | Step 14 (sau personalization) | Step 8 (sau intro7_analyzing) | Step 14 |
| Date | 18–21/06/2026 | 18–21/06/2026 | install ≥ 22/06/2026 |
| n (US only) | 4,167 | 4,207 | 10,302 |

## BigQuery Tables

```
team-begamob.iOS_Heart_Rate_CACHED_Events_03.firebase_ab_testing_corhort_all_metrics
  → experiment variant assignment (experiment='firebase_exp_63', variant='0'/'1')
  → user_pseudo_id là UPPERCASE → phải LOWER() khi join

team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE
  → screen funnel (screen_from, session_number, country, install_date)
  → denominator = splash users, session_number=1, country='United States'

team-begamob.iOS_Heart_Rate_CACHED_Events_02.SDK_PREMIUM_TRACK
  → paywall events: open / select_product / finish_purchase
  → max_date = 2026-06-21 (Rollback users chưa có data)
  → params_screen_from cần carry-forward qua LAST_VALUE IGNORE NULLS
```

## Credential

```python
CRED_PATH = r'c:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json'
# type: authorized_user → phải truyền project='team-begamob'
creds = Credentials(token=None, refresh_token=info['refresh_token'],
    client_id=info['client_id'], client_secret=info['client_secret'],
    token_uri='https://oauth2.googleapis.com/token')
client = bigquery.Client(credentials=creds, project='team-begamob')
```

## Workflow

```
queries/query_funnel_us_only.py   → data/outputs/funnel_data.json
queries/plot_butterfly_charts.py  → data/outputs/funnel_ab_exp63.html
                                     data/outputs/funnel_baseline_vs_rollback.html
                                     data/outputs/funnel_v1_vs_rollback.html
queries/query_paywall_sdk.py      → stdout (SDK_PREMIUM_TRACK purchase CVR)
```

Chạy tuần tự: query_funnel_us_only.py trước (tạo funnel_data.json), sau đó plot_butterfly_charts.py đọc file đó.

## Key Caveats

- **Country filter bắt buộc**: A/B test chỉ assign US users; Rollback là organic global (59% US). Luôn `WHERE country = 'United States'` cho cả 3 nhóm khi so sánh.
- **subscribe5_new xuất hiện 2 lần** trong funnel chart: V1 ở step 8 và Baseline ở step 14 → tách thành 2 hàng riêng khi vẽ butterfly chart.
- **SDK_PREMIUM_TRACK**: "Paywall CVR" trong bảng này = `finish_purchase / open` (purchase CVR thực). Không nhầm với `subscribe5_2 / subscribe5_new` (chỉ là screen reach ratio, không phải CVR).
- **Revenue per user Firebase**: p-value = 0.994 → chưa đạt ý nghĩa thống kê.

## Session Management

- `/note <insight>` — ghi nhanh vào `_INBOX.md`
- `/wrap` — tổng hợp session, commit, push
