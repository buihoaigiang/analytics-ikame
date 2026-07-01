# CLAUDE.md -- GSA_khong_an_kich_ban

## Description
Team đã chuẩn bị kịch bản (onboarding/flow riêng) cho user đến từ Google Search Ads (GSA), đã config sẵn trong app. Tuy nhiên thực tế user từ GSA lại không nhận được kịch bản này.

Mục tiêu điều tra: kiểm tra cách Firebase ghi nhận `attribution network name` và `traffic source name` cho các user đến từ GSA — khả năng cao là logic phân loại kịch bản trong app đang match theo network/traffic source name không đúng với giá trị thực tế mà Firebase trả về cho nhóm user này.

## Scope
- App: ios_heart_rate
- Country: US
- Date range: 2026-06-01 → 2026-07-01 (rolling 1 tháng)
- Filter: user thuộc network GSA (Google Search Ads), campaign `HoaNY _GSA_iOS_Heart_Rate - ROAS - (HeartCheck) - US - 30042026 #2`

## Data Source
- BQ Project (billing/credential): team-begamob
- Main table: `ios-heart-rate.analytics_411746096.events_*` (Firebase/GA4 export, dùng `_TABLE_SUFFIX BETWEEN 'YYYYMMDD' AND 'YYYYMMDD'` để filter theo tháng, tránh full scan)
  - `events_intraday_*` chỉ dùng để debug 1 user cụ thể trong ngày hiện tại, KHÔNG dùng cho phân tích tổng hợp nhiều ngày
- Credential: gcloud_credentials.json (DO NOT commit) — dùng file chung tại `C:\Users\admin\Desktop\gcloud_credentials.json`
- Field liên quan:
  - `traffic_source.name/medium/source` — attribution đã RESOLVE, đây là field đúng để nhận diện GSA. Không có ngay tại `first_open` cho ~16% user (xem _INBOX.md 2026-07-01)
  - `collected_traffic_source.*` (manual_source, gclid, manual_campaign_name...) — LUÔN NULL trên iOS cho kênh GSA, không dùng được để nhận diện

## Session Management
- /note <insight>
- /wrap