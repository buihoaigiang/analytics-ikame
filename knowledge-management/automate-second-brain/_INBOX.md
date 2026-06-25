# Inbox — automate-second-brain

## 2026-06-25
- [decision] Revenue thực từ web2wave: Stripe chỉ tính `invoice.payment_succeeded` → `first_purchase`; PayPal chỉ tính `PAYMENT.SALE.COMPLETED` → `first_purchase`. Web2wave normalize cả 2 về cùng `transactionType = 'first_purchase'` → filter `WHERE transactionType = 'first_purchase'` đúng cho cả 2 gateway, không cần tách

## 2026-06-25 — Wrap (transaction-providers + ios-face-scanner dashboard)
- [decision] Cột `raw` chứa đầy đủ attribution: `utm_campaign`, `user_platform`, `user_country_code`, `status` — extract bằng `JSON_VALUE(raw, '$.user_visit.utm_campaign')` etc. Bảng BQ không expose sẵn các field này
- [decision] Duplicate root cause: `double_purchase_behaviour: 1` trong price config của web2wave + Stripe webhook gửi 2 lần → mỗi transaction log 2 row cùng giây
- [pattern] Revenue column chuẩn: `CASE WHEN transactionType = 'first_purchase' THEN amount_real ELSE 0 END AS revenue`
- [bug] Looker Studio "query returned an error": dùng SELECT alias trong WHERE → fix bằng cách dùng column gốc (`createdAt` thay vì `event_date`). Cũng không thể `DATE(DATE_col, timezone)` — DATE đã convert rồi không wrap thêm timezone được
- [pattern] Looker Studio + `events_*` wildcard: luôn thêm `_TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', ...) AND FORMAT_DATE('%Y%m%d', ...)` trong WHERE để partition pruning — tránh scan full table mỗi lần load dashboard
- [pattern] `event_date` UTC+7 từ GA4: `DATE(TIMESTAMP_ADD(TIMESTAMP_MICROS(event_timestamp), INTERVAL 7 HOUR))` — hoặc ngắn hơn `DATE(createdAt, "UTC+7")` với TIMESTAMP column

## 2026-06-23 — Wrap
- [decision] README.md đặt trong `knowledge-management/automate-second-brain/` — folder này là meta-documentation về chính hệ thống, không phải code phân tích
- [pattern] Cấu trúc README 8-bước đủ để onboard từ đầu: git init → global CLAUDE.md → 3 hooks → settings.json → 2 slash commands → xong
- [decision] "new-project" là commit message convention (`new-project: <path>`), không phải slash command riêng — cần phân biệt rõ khi giải thích
- [caveat] `session_start.sh` hook chỉ chạy từ working directory mà Claude Code được mở — nếu mở từ subdirectory thì `_INBOX.md` sẽ không tự tạo ở root repo
- [pattern] Obsidian sync hoạt động bằng cách append toàn bộ `_INBOX.md` vào `Obsidian/_INBOX.md` — không dedup, cần xử lý thủ công nếu session_end chạy nhiều lần

## 2026-06-23 — Wrap (verify-cancel-android-vs-ios)
- [decision] D0 cancel rate Android thấp hơn iOS là tín hiệu thật và đáng tin — Android activation 27.8% vs iOS 36.4% (-8.6pp), trial 26.0% vs 51.0% (-25.0pp) ở US
- [decision] Product `discounted_offer` ($0.99 intro) trên Android mới là tín hiệu mạnh nhất: ever-cancel chỉ 20.7% (global) / 36.3% (US) — thấp hơn iOS activation 77.4% gần 2x
- [caveat] Ever-cancel rate cho `activation` product hội tụ về cùng điểm (74.6% cả 2 platform) — D0 thấp hơn KHÔNG đồng nghĩa retention tổng thể tốt hơn về dài hạn
- [caveat] Volume Android nhỏ hơn iOS 14x (5,832 vs 83,719 starts Jan–Jun 2026) — kết quả ổn định nhưng cần scale thêm data để confirm
- [caveat] Gap D0 trial (-25pp) có thể bị inflate bởi country mix: Android chạy nhiều PH hơn iOS, PH có D0 cancel thấp → cần country-controlled analysis để isolate behavioral signal
- [pattern] Adjust "cancellation rate" bị distort bởi event type khác nhau: iOS dùng `trial_started`, Android dùng `discounted_offer` — nếu Adjust count discounted_offer làm denominator thì Android rate trông thấp hơn rất nhiều (35.6% vs iOS 98%)
- [pattern] Apple fire cancel ngay khi user tắt auto-renewal (subscription vẫn còn hạn) → iOS `_subscription_cancelled_at_` = NULL; Google Play fire muộn hơn → Android có field này → timing event khác nhau về cơ chế
- [open] Country-controlled analysis (US-only by channel) để tách behavioral signal khỏi country mix effect
- [open] Kiểm tra Adjust dashboard đang dùng denominator nào cho cancellation rate — confirm `discounted_offer` có được tính không

## 2026-06-24 — Wrap (revenue-discrepancy-ga4-vs-adjust / ios-face-scanner)
- [decision] Không có discrepancy thực sự giữa GA4 và Adjust — nguyên nhân là timing + sandbox, không phải bug tracking
- [decision] `in_app_purchase` trên Firebase = trial start ($0) — đúng trên cả 2 platform, tương đương `trial_started` trên Adjust, revenue = $0 là chính xác
- [caveat] Revenue $142.20 trên GA4 (tuần Jun 17-23) đến từ 2 event S2S Apple↔Firebase: `app_store_subscription_renew` ($127.08) và `app_store_subscription_convert` ($7.56 sandbox) — xảy ra trước khi Adjust init thành công → Adjust không nhận được
- [caveat] Event $7.56 ngày 23/06 từ `app_store_subscription_convert` là sandbox — không tính vào revenue thực
- [caveat] BigQuery export mới connect từ Jun 11/2026 → chỉ có 14 intraday tables, chưa có finalized tables (events_YYYYMMDD) → `app_store_subscription_renew` không xuất hiện trong BQ raw vì event này chỉ được ghi vào finalized tables sau 24-72h xử lý
- [pattern] Intraday tables (`events_intraday_*`) chỉ chứa real-time device events. Server-side subscription events (renew/convert từ Apple S2S) chỉ xuất hiện trong finalized tables — cần đợi BQ export finalize mới query được
- [pattern] Khi query BQ với wildcard `events_*` mà chỉ có intraday tables, `_TABLE_SUFFIX` là `intraday_YYYYMMDD` không phải `YYYYMMDD` — filter `BETWEEN '20260617' AND '20260623'` sẽ không match → kết quả rỗng
- [open] Theo dõi khi finalized tables xuất hiện (vài ngày tới) để verify revenue S2S có đúng value không
- [open] Setup Apple S2S subscription notifications → forward sang Adjust nếu muốn Adjust track renewal revenue

## 2026-06-24 — Wrap (scan-vs-purchase-analysis)
- [decision] Dùng `first_open` làm proxy cho install trong GA4 — không có event `app_install` riêng
- [decision] `ft_face_scan` feature mới lên production từ 23/06/2026 — chỉ 1 user/ngày trong 2 ngày đầu, chưa đủ volume để kết luận
- [caveat] `status = 'success'` tồn tại trong event_params của `ft_face_scan` (22 events) — nhưng cần thêm vài ngày để có tỷ lệ ý nghĩa
- [pattern] Trong GA4 BigQuery, UNNEST event_params phải làm trong `base` CTE thành boolean flag — không thể dùng column alias trong CASE WHEN của CTE khác
- [pattern] Query pattern chuẩn: `(SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'status') = 'success' AS is_facescan_success` trong base, rồi `CASE WHEN is_facescan_success THEN user_pseudo_id END` trong aggregation CTE
- [pattern] Breakdown country dùng `geo.country` thêm vào SELECT + GROUP BY — không cần join thêm bảng
- [pattern] Timestamp GA4: `TIMESTAMP_MICROS(event_timestamp)` + `INTERVAL 7 HOUR` → UTC+7 → `DATE()`
- [open] Theo dõi tỷ lệ facescan/install khi đủ volume (kỳ vọng ~1 tuần sau launch)

## 2026-06-24 — Wrap (transaction-providers)
- [decision] Revenue thực chỉ tính từ `first_purchase` — `cancel` có `amount_real > 0` nhưng là giá trị subscription bị cancel, không phải cash nhận được
- [decision] Bảng chỉ có 3 transactionType: `first_purchase`, `cancel`, `past_due` — không có `renewal`/`rebill` → không thể tính retention thực sự với data hiện tại
- [caveat] Data mới có 2 ngày (22-23/6/2026), provider duy nhất là `web2wave`, domain duy nhất `dsblack.semantra.cloud`, gateway: Stripe + PayPal
- [caveat] Duplicate events: cùng userId + price_id + giây → 2 row với id khác nhau. Cần dedup bằng `(userId, price_id, TIMESTAMP_TRUNC(createdAt, MINUTE))` trước khi đếm giao dịch
- [caveat] 1 userId có thể mua nhiều plan khác nhau (YEARLY + Onetime GLP) — join userId trực tiếp sẽ overcount nếu không group by plan
- [pattern] Proxy retention với `nextBillingDate`: subscription plans (1-WEEK, 4-WEEK, YEARLY) = 100% có nextBillingDate; Onetime plans = 0% → phân biệt được subscription vs one-time payment
- [pattern] Cancel với nextBillingDate trong tương lai = canceled but not yet expired (user đã tắt auto-renew nhưng còn trong period)
- [open] Renewal events chưa log hoặc bảng chưa track — cần xác nhận với backend web2wave/Stripe webhook có gửi renewal event không
- [open] Retention thực sự cần đợi ít nhất 1 tuần (1-WEEK plan renew 29-30/6) để có renewal event đầu tiên
- [open] Cần làm rõ `cancel` amount: là refund hay chỉ là status log? Nếu là status log thì revenue report cần filter strict `first_purchase` only

## 2026-06-23 — Wrap (test-app/test-project-01)
- [decision] Tạo project scaffold `test-app/test-project-01` với CLAUDE.md cơ bản — chưa có analysis scope cụ thể
- [open] CLAUDE.md của test-project-01 còn trống phần Mô tả — cần điền khi đã rõ mục tiêu phân tích
- [pattern] Convention commit mới project: `new-project: <app>/<project-name>` — đồng nhất với init convention của repo
