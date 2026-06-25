# CLAUDE.md -- intro_exp63

## Description
Phân tích A/B test firebase_exp_63 (exp63) trên iOS Heart Rate app.
Mục tiêu: Tìm nguyên nhân pay rate toàn app giảm mạnh, đặc biệt variant FlowIntro14_IAP_New thấp hơn Baseline.

## Experiment Overview
- **Firebase experiment**: `firebase_exp_63` (tên trên Firebase: `AB_IAP_Intro14`)
- **Start date**: 18/06/2026
- **Variants**:
  - `Baseline`: flow intro gốc
  - `FlowIntro14_IAP_New`: thay đổi màn signin + vị trí màn subscribe
- **Split**: Baseline 4,300 users — FlowIntro14_IAP_New 4,366 users (tổng ~8,700)
- **Firebase result (7 days)**: Purchase revenue per user: Baseline $0.64 vs FlowIntro14_IAP_New $0.52 (-19%), p-value 0.994 → không có ý nghĩa thống kê theo Firebase

## Problem Statement
- Pay rate toàn app **giảm mạnh** sau khi exp63 bắt đầu (18/06/2026)
- Pay rate của **FlowIntro14_IAP_New thấp hơn Baseline** khá nhiều
- Cần tìm hiểu nguyên nhân:
  1. Funnel conversion thay đổi ở bước nào? (signin → subscribe → purchase)
  2. Variant mới có làm drop-off sớm hơn không?
  3. Có confounding factor nào không? (update app version, external traffic shift, v.v.)

## Scope
- App: iOS Heart Rate (ios-heart-rate)
- Country: (chưa xác định — kiểm tra)
- Date range: từ 18/06/2026 trở đi (so sánh pre/post nếu cần)
- Filter: chỉ users thuộc firebase_exp_63

## Data Source
- BQ Project: team-begamob
- Main table: (chưa xác định — cần explore)
- Credential: gcloud_credentials.json (DO NOT commit)

## Analysis Plan
1. Xác định bảng BQ chứa event của iOS Heart Rate
2. Lọc users thuộc exp63 theo `firebase_exp_name` hoặc `user_pseudo_id`
3. Tính funnel: install → signin → paywall_show → purchase theo từng variant
4. Tính pay rate (purchasers / total users) theo ngày và theo variant
5. So sánh pre/post 18/06 để xem pay rate drop có phải do exp không
6. Kiểm tra các metric phụ: session length, screen_view sequence, error events

## Session Management
- /note <insight>
- /wrap