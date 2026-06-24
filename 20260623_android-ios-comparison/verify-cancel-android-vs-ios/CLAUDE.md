# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mô tả
So sánh hành vi cancel subscription giữa Android Heart Rate và iOS Heart Rate
— tìm điểm khác biệt về timing, reason, cohort, D0 cancel rate.

## Scope
- App: Android Heart Rate + iOS Heart Rate
- Country: United States (primary), all countries (secondary)
- Date range: 2026-01-01 onwards (mở rộng để có đủ Android volume)

## Chạy script

```bash
# Set encoding trước khi chạy (Windows)
$env:PYTHONIOENCODING="utf-8"

python explore_schema.py      # Schema + event type breakdown
python analyze_cancel.py      # Timing distribution + cancel rate denominator
python deep_dive_android.py   # discounted_offer deep dive
python verify_d0_cancel.py    # D0 cancel rate (join by original_transaction_id)
python chart_d0_summary.py    # Chart tổng hợp → data/outputs/d0_summary.html
```

Output HTML charts: `data/outputs/`

## BigQuery setup

- Project: `team-begamob`
- Credential (authorized_user type): dùng từ `../../ios-heart-rate/funnel/intro7-vs-intro6/gcloud_credentials.json`
- Load bằng env var, KHÔNG dùng `service_account.Credentials.from_service_account_file`:

```python
import os
from google.cloud import bigquery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\admin\Desktop\analytics-ikame\ios-heart-rate\funnel\intro7-vs-intro6\gcloud_credentials.json"
client = bigquery.Client(project="team-begamob")
```

## Nguồn dữ liệu

| Platform | Bảng BQ |
|---|---|
| iOS | `team-begamob.MMP_Adjust_RawData.iOS_Heart_Rate_Raw_Export_PARTITION` |
| Android | `team-begamob.MMP_Adjust_RawData.Android_Heart_Rate_Raw_Export_PARTITION` |

- Partition filter bắt buộc: `TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("2026-01-01")`
- Base filter: `_activity_kind_ = 'subscription'`

## Quy ước query

**Subscription start events** (denominator khi tính cancel rate):
```sql
_subscription_event_type_ IN ('activation', 'trial_started', 'discounted_offer')
```

**Cancel event**: `_subscription_event_type_ = 'cancellation'`

**Join start → cancel** dùng `_subscription_original_transaction_id_` (không dùng `_adid_` vì 1 user có thể có nhiều subscription).

**D0 cancel** = `(cancel_ts - start_ts) <= 86400` giây (24h kể từ start event).

**Timestamps** đều là Unix epoch STRING → cần `CAST(... AS INT64)` trước khi tính khoảng cách.

## Kiến trúc script

```
explore_schema.py      → khám phá ban đầu, không tái dùng
analyze_cancel.py      → timing bucket + denominator comparison (global)
deep_dive_android.py   → focus discounted_offer: new vs existing subscriber?
verify_d0_cancel.py    → query chuẩn nhất: cohort-based D0 rate, join by orig_txn
chart_d0_summary.py    → hardcode kết quả từ verify_d0_cancel, vẽ chart so sánh
```

`verify_d0_cancel.py` là script authoritative — chứa query đầy đủ nhất cho D0 analysis. Khi mở rộng analysis, extend từ query này.

## Findings chính (2026-06-23)

| Metric | Android (US) | iOS (US) |
|---|---|---|
| D0 cancel — activation | 27.8% | 36.4% |
| D0 cancel — trial_started | 26.0% | 51.0% |
| Ever cancel — activation | 74.6% | 74.6% |
| Ever cancel — discounted_offer | 36.3% | — |

- **iOS trigger**: Apple fire `DID_CHANGE_RENEWAL_STATUS` ngay khi tắt auto-renewal → `_subscription_cancelled_at_` = NULL, cancel xảy ra khi sub vẫn còn hiệu lực
- **Android trigger**: Google Play fire `SUBSCRIPTION_CANCELED` → có `_subscription_cancelled_at_` — 53.7% cancel xảy ra sau 7+ ngày
- **Distortion trong Adjust dashboard**: Android dùng `discounted_offer` thay vì `activation` cho product $0.99 → nếu Adjust count `discounted_offer` vào denominator thì Android rate = 35.6% vs iOS 98% (không phải behavioral difference thuần túy)

## Open questions
- Country-controlled analysis (US-only by UA channel) để loại country mix effect
- Confirm Adjust dashboard denominator: `discounted_offer` có được count không?
