# CLAUDE.md -- dashboard

## Description
Dashboard theo dõi performance cho webfunnel. Mục tiêu: explore các bảng BQ liên quan và tạo dashboard khớp với report hiện có.

## Scope
- App: webfunnel
- Country:
- Date range:
- Filter:

## Platforms
| Platform | Payment gateway | Data status |
|----------|-----------------|--------------|
| web2wave | Stripe | Đã có data, đã chạy |
| funnel_fox | Paddle | Chưa có data, đã chạy (cần kiểm tra pipeline/table) |

## Data Source
- BQ Project: `ikame-apps-dev` (dataset `tracking_transaction_providers`) — KHÔNG phải team-begamob
- Main tables:
  - `ikame-apps-dev.tracking_transaction_providers.stripe-raw-2` — Stripe webhook raw (web2wave/Stripe)
  - `ikame-apps-dev.tracking_transaction_providers.web2wave-raw` — Web2Wave webhook raw (gồm cả Stripe + PayPal)
  - funnel_fox/Paddle: chưa xác định bảng
- Schema chi tiết + ý nghĩa cột: [docs/schema_stripe_web2wave.md](docs/schema_stripe_web2wave.md)
- Credential: gcloud_credentials.json (DO NOT commit)
- KHÔNG tự ý explore schema/dataset/table. Chỉ query khi user chỉ định rõ dataset/table cần xem.

## Quy ước quan trọng (rút ra từ session)
- Query revenue: KHÔNG join `stripe-raw-2` vào `web2wave-raw` — dùng trực tiếp `web2wave-raw`, filter `event_type IN ('charge.succeeded','PAYMENT.CAPTURE.COMPLETED','PAYMENT.SALE.COMPLETED') AND real_payment=1`.
- Filter ngày dùng timezone `Asia/Ho_Chi_Minh`, không dùng UTC thô.
- `product_type` phân loại theo `price_label`, KHÔNG dùng `plan_name`.
- Pipeline dùng webhook, không backfill lịch sử → luôn có "id mồ côi P0" (xem `docs/schema_stripe_web2wave.md`).
- Dashboard Looker Studio "webfunnel" đã có 3 data source (transaction / retention / mồ côi P0) — chi tiết ở `_INBOX.md`.

## Session Management
- /note <insight>
- /wrap