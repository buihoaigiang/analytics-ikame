# CLAUDE.md -- revenue-discrepancy-ga4-vs-adjust

## Description
Điều tra chênh lệch revenue giữa GA4 và Adjust cho app iOS Face Scanner.
GA4 ghi nhận revenue (ví dụ: $83.17 ngày 22/06/2026) nhưng Adjust không có dữ liệu tương ứng.
Mục tiêu: tìm nguyên nhân từ raw event data.

## Scope
- App: ios-face-scanner
- Date range: từ Jun 17, 2026 (dựa theo screenshot Firebase console)
- Event quan tâm: `in_app_purchase`

## Data Source
- BQ Project: team-begamob
- GA4 raw table: `ios-face-scanner.analytics_540983063.events_*`
- Credential: gcloud_credentials.json (DO NOT commit)

## Key Query
```sql
SELECT *
FROM `ios-face-scanner.analytics_540983063.events_*`
WHERE event_name IN ('in_app_purchase')
```

## Context — RESOLVED (2026-06-24)
- `in_app_purchase` = trial start → $0 revenue — đúng trên cả GA4 và Adjust
- $142.20 GA4 đến từ `app_store_subscription_renew` (S2S Apple↔Firebase), xảy ra trước Adjust init
- $7.56 ngày 23/06 là sandbox, không tính
- Adjust $0 là đúng — chưa nhận S2S subscription events từ Apple
- **Không có discrepancy thực sự**

## BQ Notes
- Chỉ có `events_intraday_*` (mới connect Jun 11/2026), chưa có finalized tables
- `app_store_subscription_renew` chỉ xuất hiện trong finalized tables — không có trong intraday
- Khi dùng `events_intraday_*`: `_TABLE_SUFFIX` = `YYYYMMDD` (phần sau `intraday_`)

## How to run
```bash
PYTHONIOENCODING=utf-8 python analyze.py
```

## Session Management
- /note <insight>
- /wrap