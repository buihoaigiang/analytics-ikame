## 2026-07-02 — Wrap

- [decision] Query revenue dùng trực tiếp `web2wave-raw` (KHÔNG join `stripe-raw-2`) — vì `stripe-raw-2` không có event `charge.succeeded`, nếu join theo `stripe_event_type='customer.subscription.created'` chỉ bắt được ~24% doanh thu thật (bỏ sót toàn bộ renewal).
- [decision] Filter "tiền thật đã thu": `event_type IN ('charge.succeeded','PAYMENT.CAPTURE.COMPLETED','PAYMENT.SALE.COMPLETED') AND real_payment = 1`. KHÔNG thêm `status='active'` (xem caveat race condition).
- [decision] Timezone filter ngày dùng `Asia/Ho_Chi_Minh`, không dùng UTC thô — verify khớp đúng số "Successful payments" hiển thị trên Stripe Home (96 vs 37 nếu dùng UTC).
- [decision] `product_type` (subscription/onetime) phân loại theo `price_label` (chứa `Lifetime`/đơn vị thời gian), KHÔNG dùng `plan_name` — string-match trên `plan_name` sai 4/13 plan (68 dòng) do tên marketing không chứa từ khóa thời gian.
- [decision] Revenue tính bằng `SUM(amount_real)`, KHÔNG dùng `total_revenue` (đây là số lũy kế theo subscription, cộng dồn sẽ đếm trùng).
- [decision] Transaction ID = ghép `(id, charges_count)` — không có cột đơn lẻ nào unique theo transaction (`id`/`pay_system_id` là ID subscription, lặp lại qua nhiều lần charge).
- [decision] Retention subscription tính theo `charges_count` (P0 = charges_count=1, mẫu số cố định = P0 cho mọi Pn), theo yêu cầu user — bỏ qua time-window thực tế để đơn giản hoá.
- [decision] Các dim ổn định (plan_name, country, campaign, url_host, gateway, product_type) lấy bằng `ANY_VALUE()` trong 1 lần `GROUP BY id` duy nhất — không tách CTE riêng theo charges_count cụ thể (tránh bug tự-loại nhóm chưa kịp renew).

- [caveat] Cả `stripe-raw-2` và `web2wave-raw` là **append-only log webhook**, không phải snapshot trạng thái — mỗi row = 1 lần webhook, không dedup sẵn.
- [caveat] Pipeline dùng webhook, **không backfill lịch sử trước ngày setup** (`web2wave-raw` có data từ 2026-06-27) → sinh ra "id mồ côi P0": subscription có charges_count>=2 nhưng KHÔNG có dòng charges_count=1 trong bảng (verify: 82 id mồ côi tại thời điểm wrap, 100% có min_charge=2, tập trung ở `1-WEEK PLAN` 73/82).
- [caveat] **Bug tinh vi đã fix**: khi tính retention theo cohort_date (`MIN(event_date)` per id), id mồ côi bị gắn nhầm ngày renewal thành ngày cohort → tạo giả tượng "mua và renew ngay trong cùng 1 ngày" (case thật: Jul1/1-WEEK PLAN hiển thị P0=78/P1=17/22%, nhưng đúng ra P0=61/P1=0/0% sau khi loại mồ côi bằng `HAVING MIN(charges_count) = 1`). Verify: cả 17 case "renew" đều có `first_ts = second_ts` (cùng 1 dòng duy nhất).
- [caveat] Với data hiện tại (~5 ngày kể từ khi webhook chạy), **chưa có renew thật nào xảy ra** cho `1-WEEK PLAN` dù cohort xa nhất đã qua 4 ngày (cần ~7 ngày mới đủ 1 chu kỳ) — mọi số "P1>0" quan sát được trước khi fix bug mồ côi đều là artifact, không phải retention thật.
- [caveat] Retention theo `charges_count` hiện KHÔNG phân biệt "chưa đủ thời gian để renew" vs "thực sự churn" — 2 trường hợp gộp chung thành `retained=0`. Muốn tách cần thêm cột `days_elapsed = DATE_DIFF(CURRENT_DATE, event_date, DAY)` và so với chu kỳ billing thật của từng plan (không lấy tự động từ `price_label` vì không đáng tin, xem caveat dưới).
- [caveat] `price_label` có 2 phần (giá trial → giá recurring) nhưng **tên plan không khớp giá trial** — `1-WEEK PLAN` có `price_label = "7.99 usd / 7 days → 29.96 usd / 1 month"` nhưng 100% charge quan sát được đều ở mức $29.96 (giá recurring), không có charge nào ở $7.99. Nên KHÔNG dùng tên plan để suy đoán chu kỳ billing thật.
- [caveat] Không có event `charge.failed`/`invoice.payment_failed`, không có cột `decline_reason` trong 2 bảng — muốn phân tích txn fail phải lấy trực tiếp từ Stripe.
- [caveat] `status` trên dòng real-charge không phải luôn `active` (race condition giữa 2 webhook Stripe gửi gần nhau, KHÔNG phải lỗi/hoàn tiền) — không filter theo status khi tính revenue.
- [caveat] Stripe "Gross volume" ở Home ≠ `SUM(amount_real)` — 2 metric khác định nghĩa (ngay trong Stripe, Gross volume và Payments→Succeeded cũng lệch nhau ~35%), không nên đối chiếu 2 số này với nhau.
- [caveat] BigQuery không có hàm `URL_DECODE` built-in — decode UTM percent-encoded (`%20`/`%2B`/`%28`/`%29`/`%26`) phải làm thủ công bằng chain `REPLACE`.

- [pattern] Build retention curve "không hardcode cột Pn": dùng `GENERATE_ARRAY` sinh long-format (`id` × `period` × cờ `retained` 0/1), rồi dùng Pivot Table trong Looker Studio tự pivot `period` thành cột — không cần sửa SQL khi có thêm period mới.
- [pattern] `AVG()` trên cột cờ 0/1 = % retention trực tiếp (không cần viết công thức chia tay).
- [pattern] Muốn 1 chart Looker Studio đổi được breakdown dimension mà không sửa SQL: tạo Parameter (Text, allowed values) + Calculated field CASE WHEN theo parameter + Parameter control dropdown trên trang.
- [pattern] Field từ BigQuery Custom Query trong Looker Studio luôn vào Dimensions hết — muốn có Metric phải tạo Calculated Field mới với hàm aggregate (`SUM()`/`AVG()`) trong formula, không có nút "Convert to Metric" trong menu field.

- [open] funnel_fox/Paddle: chưa tìm được bảng data tương ứng trong dataset `tracking_transaction_providers` — cần hỏi lại vị trí bảng khi bắt đầu phần đó.
- [open] Chưa xác định N (số ngày/chu kỳ billing thật) cho từng plan để tách "chưa đủ thời gian" vs "churn thật" trong retention — cần đo thực nghiệm qua thời gian dài hơn (không lấy từ `price_label`).
- [open] Cần theo dõi số lượng id "mồ côi P0" có giảm dần về 0 theo `first_seen_date` không (data sạch dần theo thời gian) — đã có query stats sẵn, chưa built chart theo dõi trend này.

## Dashboard build status (Looker Studio "webfunnel")
3 data source đã tạo trên BigQuery custom query:
1. `web2wave-raw` — transaction chi tiết (revenue, UTM, country, product_type) filter theo `@DS_START_DATE`/`@DS_END_DATE`
2. `web2wave-raw retention` — cohort P0→Pn theo `charges_count`, đã fix bug mồ côi (`HAVING MIN(charges_count) = 1`)
3. `web2wave-raw user no p0` — thống kê riêng nhóm mồ côi (82 user tại thời điểm wrap)

Full schema + toàn bộ query đã validate: [docs/schema_stripe_web2wave.md](docs/schema_stripe_web2wave.md)
