# Inbox — automate-second-brain

## 2026-06-25 — Wrap (exp63 iOS Heart Rate — intro_exp63)
- [decision] **Tắt vĩnh viễn FlowIntro14_IAP_New, giữ Baseline**: V1 chèn paywall ở step 8 (trước personalization) → +6.5pp paywall reach nhưng mất -13.8% purchases. CVR thấp hơn 2.1pp (7.2% vs 9.3%). Personalization flow quyết định willingness-to-pay, không phải thời điểm hiển thị paywall.
- [caveat] **Country confounding trong Rollback**: Rollback unfiltered = 59.1% US + 41% Brazil/Spain/India. A/B test (Baseline/V1) = 100% US. Nếu không filter cùng country → apparent CVR drop 4.3pp là artifact, không phải user quality thật. Sau US-only filter: Rollback ≈ Baseline ở mọi metric.
- [caveat] **Tên metric sai trong report ban đầu**: "Paywall CVR" = subscribe5_2/subscribe5_new (tỷ lệ reach screen thứ 2, không phải purchase CVR). "Subscribe rate" = subscribe5_2/splash (reach rate, không phải subscription rate). Purchase CVR thực = finish_purchase/view từ SDK_PREMIUM_TRACK.
- [caveat] **SDK_PREMIUM_TRACK data lag**: max_date = 2026-06-21 → Rollback users (install ≥22/06) chưa có purchase data. Không thể kết luận purchase CVR cho Rollback cho đến khi data cập nhật.
- [caveat] **Revenue per user không significant**: Firebase UI: $0.64 vs $0.52 (−19%), p-value = 0.994. 7 ngày với n≈8,700 chưa đủ power để kết luận thống kê cho IAP A/B test.
- [pattern] **Luôn filter cùng country khi so sánh cohorts**: Nếu nhóm A chỉ assign 1 country (A/B test US-only) nhưng nhóm B là organic global, phải filter cùng country TRƯỚC khi so sánh. Không filter → country composition khác → CVR gap giả tạo.
- [pattern] **Paywall sớm ≠ CVR tốt**: Increasing paywall reach bằng cách đặt paywall trước value delivery thường backfire. User chưa thấy giá trị → thấp willingness-to-pay → CVR giảm bù lại volume tăng. Net = revenue giảm.
- [open] Sign_in Rollback thấp hơn Baseline 1.1pp (95.4% vs 96.5%) — PM confirm không có thay đổi UI. Cần investigate khi có thêm data.
- [open] Rollback purchase CVR: cần chờ SDK_PREMIUM_TRACK sau 22/06 để xác nhận.

---
⚠️ Note: Entry "2026-06-25 — exp63 iOS Heart Rate (update: Rollback analysis)" bên dưới chứa kết luận SAI (dựa trên Rollback unfiltered + filter intro7). Đã sửa trong session này — xem Obsidian note.
---

## 2026-06-25 — exp63 iOS Heart Rate (update: Rollback analysis)
- [caveat] "Rollback" (≥22/06/2026, n=17,439) KHÔNG phải rollback về Baseline. PM đã deploy flow mới: subscribe5_new xuất hiện ở step 2 (sau sign_in_onboarding, 70.9%) — còn sớm hơn cả V1 (step 7). Paywall CVR Rollback = 13.8% (9.8/70.9) — TỆ NHẤT trong 3 nhóm.
- [decision] Paywall CVR 3 nhóm: Baseline 25.0% (16.2/64.7) > V1 24.4% (17.3/70.8) > Rollback 13.8% (9.8/70.9) → mỗi lần chèn paywall sớm hơn, CVR càng giảm. Học được: user cần trải nghiệm giá trị TRƯỚC khi thấy paywall.
- [pattern] Funnel Rollback (≥22/06): splash(100) → sign_in(94) → subscribe5_new(70.9) → intro7_heart_measure(60.3) → ... → new_home_v2(32.1) → subscribe5_2(9.8). subscribe5_2 thấp hơn nhiều Baseline (16.2%) và V1 (17.3%).
- [open] Cần xác nhận với PM: deploy ≥22/06 là gì? Có phải intentional test với paywall ở step 2 không? Hay bug?
- [pattern] Khi vẽ butterfly chart với 3+ flow khác nhau: mỗi variant cần tách riêng hàng subscribe5_new tại đúng vị trí; dùng ⚡ prefix + amber (#C4720A) để highlight diverge point.

## 2026-06-25 — exp63 iOS Heart Rate
- [caveat] PM thay đổi A/B test (firebase_exp_63) một cách tùy tiện, không đúng tinh thần A/B test: variant FlowIntro14_IAP_New chèn subscribe5_new sớm (sau intro7_check_apple_watch, step 7) thay vì sau intro7_final_processing (step 14) như Baseline → làm vỡ toàn bộ personalization flow, pay rate giảm mạnh
- [pattern] subscribe5_new xuất hiện ở 2 vị trí khác nhau giữa Baseline (step 14, sau final_processing, 64.7%) vs V1 (step 7, sau check_apple_watch, 70.8%) → khi vẽ funnel butterfly chart cần tách thành 2 hàng riêng, không dùng chung 1 hàng
- [decision] Paywall CVR: Baseline 40.7% vs FlowIntro14 19.9% (−20.7pp) — nguyên nhân: user chưa qua personalization nên chưa thấy đủ giá trị khi bị chặn paywall sớm
- [open] Cần confirm với PM: exp63 có phải test đúng hypothesis không, hay chỉ là thay đổi ad-hoc mà không có hypothesis rõ ràng trước?
- [pattern] Cách tạo funnel butterfly chart A/B (exp63):
  1. AB table: `iOS_Heart_Rate_CACHED_Events_03.firebase_ab_testing_corhort_all_metrics` WHERE experiment='firebase_exp_63' → variant 0=Baseline, 1=FlowIntro14
  2. Screen table: `iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE` WHERE session_number=1 AND install_date>='2026-06-18', group by (uid, screen_from)
  3. Join: AB table dùng UPPERCASE user_pseudo_id → phải LOWER() trước khi join với screen table (lowercase)
  4. Tính % = COUNT(DISTINCT uid) / total_ab per variant
  5. subscribe5_new xuất hiện ở 2 vị trí khác nhau → tách thành 2 hàng riêng: [V1 step 7, sau check_apple_watch] và [Baseline step 14, sau final_processing]
  6. Plotly butterfly: Baseline bars x âm (đi trái), V1 bars x dương (đi phải); `include_plotlyjs=True` để tự-chứa (không dùng CDN)
  7. Script: `20260625_ios_heart_rate_exp63/intro_exp63/data/outputs/funnel_ab_exp63.html`

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
