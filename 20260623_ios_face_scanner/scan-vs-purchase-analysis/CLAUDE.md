# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mô tả
Phân tích tỷ lệ sử dụng FaceScan / Purchase / Install theo ngày và country cho app iOS Face Scanner.

- **App GA4**: `ios-face-scanner` — dataset `analytics_540983063`
- **BQ Project**: `team-begamob`
- **Credential**: `gcloud_credentials.json` (authorized_user, KHÔNG commit)

## Chạy scripts

```powershell
# Query dữ liệu từ BigQuery → CSV
python query_ratios.py

# Tạo chart HTML
python visualize_ratios.py

# Khám phá event params của ft_face_scan
python check_facescan_params.py
```

## Cấu trúc

```
scan-vs-purchase-analysis/
├── query_ratios.py          ← query chính, xuất CSV
├── visualize_ratios.py      ← Plotly chart từ CSV
├── check_facescan_params.py ← debug event_params
└── data/outputs/            ← CSV + HTML chart
```

## BigQuery — Events cần theo dõi

| Event | Ý nghĩa |
|---|---|
| `first_open` | Install (proxy) |
| `ft_face_scan` | User bắt đầu scan |
| `ft_face_scan` + `status='success'` | Scan thành công |
| `in_app_purchase` | Purchase |

## Query pattern chuẩn

Event params trong GA4 phải UNNEST trong `base` CTE rồi tính boolean flag — **không** dùng alias trong CASE WHEN của CTE khác:

```sql
WITH base AS (
  SELECT
    user_pseudo_id,
    event_name,
    geo.country AS country,
    DATE(TIMESTAMP_ADD(TIMESTAMP_MICROS(event_timestamp), INTERVAL 7 HOUR)) AS event_date,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'status') = 'success'
      AS is_facescan_success
  FROM `ios-face-scanner.analytics_540983063.events_*`
  WHERE event_name IN ('ft_face_scan', 'in_app_purchase', 'first_open')
)
```

- Timestamp: `TIMESTAMP_MICROS(event_timestamp)` + `INTERVAL 7 HOUR` → UTC+7
- Dùng `SAFE_DIVIDE` để tránh chia cho 0
- Dùng `events_*` wildcard; filter ngày qua `_TABLE_SUFFIX` nếu cần tối ưu cost

## Session Management
- `/note <insight>` — ghi nhanh vào `_INBOX.md`
- `/wrap` — tổng hợp session + git commit
