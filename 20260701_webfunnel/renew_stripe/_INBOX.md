# _INBOX.md — renew_stripe

## 2026-07-01 — Wrap
- [caveat] Bảng Stripe của Huy (BE) lấy trực tiếp từ cổng Stripe, không phải từ server nội bộ
- [caveat] Khi user renew, subscription_id **không đổi** → không thể dùng sub_id để phân biệt renewal vs new sub
