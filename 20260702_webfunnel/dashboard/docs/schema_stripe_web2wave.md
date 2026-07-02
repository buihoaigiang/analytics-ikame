# Schema — Stripe raw & Web2Wave raw (webfunnel dashboard)

> Explored: 2026-07-02. Nguồn: BigQuery `ikame-apps-dev.tracking_transaction_providers`, đối chiếu với Stripe API docs (docs.stripe.com) và Web2Wave webhook docs (docs.web2wave.com/reference/webhook-formats).

## Tổng quan
Cả 2 bảng đều là **append-only log các webhook event nhận được**, KHÔNG phải bảng current-state — mỗi row = 1 lần webhook được gửi/nhận (nhiều row có thể trùng `id`/`stripe_subscription_id` với `event_type`/`stripe_event_type` khác nhau theo thời gian). Khi tính revenue/MRR cần dedup hoặc filter theo loại event tương ứng với "tiền thực sự được charge" (xem mục Caveats).

---

## 1. `ikame-apps-dev.tracking_transaction_providers.stripe-raw-2`
Webhook event thô từ **Stripe** (dùng cho platform **web2wave** — cổng Stripe). 599 rows tại thời điểm explore.

| Cột | Type | Ý nghĩa |
|-----|------|---------|
| `created_at` | TIMESTAMP | Thời điểm record được ingest vào BQ (ETL insert time), không phải thời điểm Stripe tạo event |
| `id_record` | STRING | ID event của Stripe (`evt_...`) — định danh duy nhất cho mỗi lần webhook được gửi |
| `stripe_created` | INTEGER | Unix timestamp (giây) — thời điểm **Stripe** tạo event (field `created` của Event object) |
| `stripe_subscription_id` | STRING | ID subscription liên quan (`sub_...`) |
| `live_mode` | BOOLEAN | `true` = giao dịch thật (live mode), `false` = test mode. Data hiện tại: 591 live / 13 test |
| `stripe_event_type` | STRING | Loại webhook event. Giá trị quan sát được: `customer.subscription.updated` (340), `customer.subscription.created` (178), `customer.subscription.deleted` (83), `invoice.payment_succeeded` (3) |
| `collection_method` | STRING | Cách thu tiền của subscription: `charge_automatically` (tự trừ tiền) hoặc `send_invoice` (gửi hoá đơn). Data hiện tại toàn bộ là `charge_automatically` |
| `currency` | STRING | Mã tiền tệ ISO (vd `usd`). 3 row bị rỗng — đều thuộc event `invoice.payment_succeeded` (field currency không map trong payload này) |
| `customer` | STRING | ID khách hàng Stripe (`cus_...`) |
| `start_date` | INTEGER | Unix timestamp — ngày subscription bắt đầu (khác `created` nếu có backdating) |
| `trial_start` | INTEGER | Unix timestamp — ngày bắt đầu trial. Trong data hiện tại luôn bằng `start_date` (nghĩa là mọi subscription đều bắt đầu bằng trial) |
| `price` | INTEGER | Giá plan tính theo **cent** (đơn vị nhỏ nhất của currency, theo convention Stripe). Vd `2996` = $29.96 |

### Ý nghĩa các `stripe_event_type` xuất hiện trong data
- `customer.subscription.created` — subscription mới được tạo (thường ngay sau khi user nhập thẻ / bắt đầu trial)
- `customer.subscription.updated` — subscription có thay đổi (đổi trạng thái trial→active, đổi plan, gia hạn, v.v.) — chiếm tỉ trọng lớn nhất, cần lọc kỹ khi dùng cho revenue
- `customer.subscription.deleted` — subscription kết thúc/bị huỷ hẳn
- `invoice.payment_succeeded` — một lần thanh toán hoá đơn thành công (đây là event gần nhất với "tiền thật đã thu", nhưng số lượng rất ít trong data hiện tại → nghi ngờ pipeline ingest chưa bắt đủ event này)

---

## 2. `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
Webhook event thô từ **Web2Wave** (platform quiz/funnel, nhận webhook từ cả Stripe và PayPal do Web2Wave forward lại). 2410 rows tại thời điểm explore.

| Cột | Type | Ý nghĩa |
|-----|------|---------|
| `type` | STRING | Loại object webhook, luôn là `subscription` trong data hiện tại |
| `id` | INTEGER | ID subscription nội bộ của Web2Wave |
| `user_id` | STRING | GUID định danh user trong hệ thống Web2Wave |
| `user_email` | STRING | Email khách hàng (rỗng trong data hiện tại — có thể do ẩn/không map) |
| `created_at` | STRING | Thời điểm subscription được tạo (ISO string) |
| `updated_at` | STRING | Thời điểm cập nhật gần nhất |
| `payment_system` | INTEGER | Mã số hệ thống thanh toán (nội bộ Web2Wave) |
| `payment_system_label` | STRING | Tên cổng thanh toán: `Stripe` (2391) hoặc `PayPal` (40) |
| `real_payment` | INTEGER | `1` = giao dịch thật (production), `0` = test mode |
| `pay_system_id` | STRING | ID subscription bên hệ thống thanh toán gốc (`sub_...` cho Stripe) |
| `project_domain` | STRING | Domain của project/funnel (vd `ikame-global.web2wave.com`) |
| `quiz_id` / `quiz_name` | STRING | ID/tên quiz dẫn đến subscription này (null nếu không qua quiz) |
| `paywall_id` / `paywall_name` | STRING | ID/tên paywall hiển thị lúc convert |
| `price_id` | STRING | ID định danh giá/plan bên hệ thống thanh toán (`price_...`) |
| `plan_name` | STRING | Tên plan nội bộ Web2Wave (vd `TRAIL-FLOW`) |
| `price_label` | STRING | Label hiển thị giá (vd `13.98 usd / 1 week`) |
| `price_description` | STRING | Mô tả chi tiết plan |
| `amount` | STRING | Số tiền tính theo **cent**, dạng string (vd `"1398.00"` = 1398 cent = $13.98) |
| `amount_real` | FLOAT | Số tiền thực theo đơn vị tiền tệ chính (vd `13.98` USD) — dùng field này cho revenue, KHÔNG dùng `amount` |
| `currency` | STRING | Mã tiền tệ. Data hiện tại: `usd` (2379), `USD` (40 — case khác, cần LOWER() khi group), `hkd` (12) |
| `canceled_at` | STRING | Thời điểm huỷ (null nếu chưa huỷ) |
| `cancel_at_period_end` | INTEGER | Cờ huỷ ở cuối kỳ thanh toán hiện tại (0/1) |
| `customer` | STRING | ID khách hàng bên hệ thống thanh toán (Stripe `cus_...`) |
| `status` | STRING | Trạng thái subscription. Data hiện tại: `active` (1123), `incomplete` (594), `past_due` (454), `canceled` (260). Các giá trị khác có thể xuất hiện theo docs: `trialing`, `incomplete_expired`, `unpaid`, `paused` |
| `cancel_scheduled` | STRING | `"Yes"`/`"No"` — có lịch huỷ trước hay không |
| `next_charge_date` | STRING | Ngày charge tiếp theo dự kiến |
| `last_charge_date` | STRING | Ngày charge gần nhất |
| `charges_count` | INTEGER | Tổng số lần đã charge thành công cho subscription này |
| `phases_num` | INTEGER | Số "phase" giá của subscription (vd trial phase → paid phase) |
| `total_revenue` | NUMERIC | Tổng doanh thu tích lũy của subscription tính theo **cent** (vd `6990` = $69.90 cho 5 lần charge $13.98) |
| `manage_link` | STRING | Link customer portal để user tự quản lý subscription |
| `plan_id` | INTEGER | ID nội bộ của plan (đi kèm `plan_name`) |
| `user_agent` | STRING | User agent lúc checkout |
| `ip` | STRING | IP lúc checkout |
| `url` | STRING | URL trang checkout |
| `user_zip_code` / `user_country_code` / `user_state_code` / `user_city_name` | STRING | Thông tin geo suy ra từ IP/billing lúc checkout |
| `user_language` | STRING | Ngôn ngữ browser user |
| `user_platform` | STRING | Platform/OS lúc checkout (web/mobile...) |
| `send_event_name` | STRING | Tên event gửi đi cho ad platform/tracking (data hiện tại toàn bộ là `Purchase`) |
| `send_event_amount` | FLOAT | Giá trị gửi kèm event tracking (thường = `amount_real` tại thời điểm gửi) |
| `event_type` | STRING | Event gốc từ cổng thanh toán đã trigger row này. Data hiện tại: `customer.subscription.updated` (1065), `customer.subscription.created` (594), `charge.succeeded` (480), `customer.subscription.deleted` (252) — 4 loại này từ **Stripe**; `BILLING.SUBSCRIPTION.ACTIVATED` (17), `PAYMENT.SALE.COMPLETED` (12), `BILLING.SUBSCRIPTION.CANCELLED` (8), `PAYMENT.CAPTURE.COMPLETED` (3) — 4 loại này từ **PayPal** |

### Lưu ý các cột hiện đang "chết" (1 giá trị duy nhất, chưa chắc đúng cho toàn bộ data)
`type` (luôn `subscription`), `cancel_scheduled` (luôn `No`), `send_event_name` (luôn `Purchase`), `cancel_at_period_end` (luôn `0`) — cần re-check khi data lớn hơn, không nên coi là hằng số vĩnh viễn.

---

## Caveats khi build dashboard
1. **Cả 2 bảng là log webhook, không phải snapshot trạng thái** → nếu tính "số subscription active hiện tại" phải lấy trạng thái mới nhất theo `(id/stripe_subscription_id, updated_at)`, không COUNT thẳng số row.
2. **Revenue**: dùng `charge.succeeded` (Stripe) / `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.SALE.COMPLETED` (PayPal) trong `event_type` của `web2wave-raw` làm event đại diện cho "tiền đã thu thật" — tránh double-count khi cùng 1 subscription có nhiều row `customer.subscription.updated`.
3. **`web2wave-raw` gộp cả Stripe và PayPal** (`payment_system_label`) — bảng `stripe-raw-2` chỉ chứa phần Stripe thuần từ web2wave nên có thể dùng để cross-check số liệu Stripe, nhưng `stripe-raw-2` KHÔNG có `amount`/`price` thực tế đã charge (chỉ có `price` = giá plan), nên revenue nên lấy từ `web2wave-raw.amount_real`/`total_revenue`.
4. **Currency case-sensitivity**: `web2wave-raw.currency` có cả `usd` và `USD` → cần `LOWER(currency)` khi group.
5. **funnel_fox/Paddle**: chưa có bảng data tương ứng trong dataset này — cần hỏi lại vị trí bảng khi bắt đầu phần đó.
6. **Không cần join sang `stripe-raw-2` để lấy transaction thật** — bảng này không có event `charge.succeeded` (chỉ có `created`/`updated`/`deleted`/`invoice.payment_succeeded` với rất ít row), nên không thể dùng làm bảng gốc để xác định "tiền thật đã thu". `web2wave-raw` đã forward nguyên event + có sẵn `url`/`plan_name`/`price_label`/`user_email`/`amount_real`, đủ để lấy transaction thật cho cả Stripe và PayPal mà không cần join.

### Query chuẩn — transaction thu tiền thật (Stripe + PayPal) + bóc UTM từ `url`
Đã validate: join sang `stripe-raw-2` theo `stripe_event_type = 'customer.subscription.created'` chỉ bắt được charge đầu tiên, bỏ sót renewal → chỉ capture ~24% doanh thu thật. Dùng trực tiếp `web2wave-raw`, không join. `charges_count = 1` → `new`, `> 1` → `renew` (verify: 410 new / 71 renew trên 481 dòng `charge.succeeded`). Cột `url` được bóc thành `url_host`/`url_path`/UTM (percent-encoded, decode thủ công qua `REPLACE` vì BigQuery không có `URL_DECODE` built-in). Toàn bộ đã test chạy đúng trên data thật (482 dòng).

```sql
WITH base AS (
  SELECT
    PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at) AS event_timestamp,  -- UTC
    DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at), 'Asia/Ho_Chi_Minh') AS event_date,  -- giờ VN, khớp cách Stripe hiển thị "ngày"
    id, user_id, user_email, pay_system_id, customer,
    payment_system_label,      -- Stripe / PayPal
    plan_name, price_label, url,
    amount_real, currency,
    user_country_code,         -- geo suy ra từ IP/billing lúc checkout, 0/507 dòng rỗng trên real-charge
    status, event_type,
    charges_count,
    CASE WHEN charges_count = 1 THEN 'new' ELSE 'renew' END AS txn_type,  -- charges_count = số lần charge thành công tính đến dòng webhook này
    CASE
      WHEN REGEXP_CONTAINS(LOWER(price_label), r'lifetime') THEN 'onetime'
      WHEN REGEXP_CONTAINS(LOWER(price_label), r'day|week|month|year') THEN 'subscription'
      ELSE 'other'
    END AS product_type,  -- dùng price_label, không dùng plan_name (xem mục Phân loại product_type)
    NET.HOST(url) AS url_host,
    REGEXP_EXTRACT(url, r'^https?://[^/]+([^?]*)') AS url_path,
    REGEXP_EXTRACT(url, r'[?&]utm_source=([^&]*)') AS utm_source,
    REGEXP_EXTRACT(url, r'[?&]utm_medium=([^&]*)') AS utm_medium,
    REGEXP_EXTRACT(url, r'[?&]utm_campaign=([^&]*)') AS utm_campaign_raw,
    REGEXP_EXTRACT(url, r'[?&]utm_campaign_id=([^&]*)') AS utm_campaign_id,
    REGEXP_EXTRACT(url, r'[?&]utm_content=([^&]*)') AS utm_content_raw,
    REGEXP_EXTRACT(url, r'[?&]utm_term=([^&]*)') AS utm_term_raw,
    REGEXP_EXTRACT(url, r'[?&]utm_id=([^&]*)') AS utm_id,
    REGEXP_EXTRACT(url, r'[?&]utm_ad_id=([^&]*)') AS utm_ad_id,
    REGEXP_EXTRACT(url, r'[?&]utm_adset_id=([^&]*)') AS utm_adset_id,
    REGEXP_CONTAINS(url, r'[?&]fbclid=') AS has_fbclid
  FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
  WHERE
    event_type IN ('charge.succeeded', 'PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.SALE.COMPLETED')
    AND real_payment = 1
)
SELECT
  event_timestamp, event_date, id, user_id, user_email, pay_system_id, customer,
  payment_system_label,
  plan_name, price_label, url,
  url_host, url_path,
  utm_source, utm_medium,
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(utm_campaign_raw,'%20',' '),'%2B','+'),'%28','('),'%29',')'),'%26','&') AS utm_campaign,
  utm_campaign_id,
  REPLACE(REPLACE(utm_content_raw,'%20',' '),'%2B','+') AS utm_content,
  REPLACE(REPLACE(utm_term_raw,'%20',' '),'%26','&') AS utm_term,
  utm_id, utm_ad_id, utm_adset_id, has_fbclid,
  amount_real, currency, user_country_code,
  status, event_type,
  charges_count, txn_type, product_type
FROM base
WHERE 1=1
  AND event_date BETWEEN PARSE_DATE('%Y%m%d', @DS_START_DATE) AND PARSE_DATE('%Y%m%d', @DS_END_DATE)  -- Looker Studio date-range control
ORDER BY event_timestamp DESC
```

Bản dùng trong Looker Studio (custom query) filter theo `@DS_START_DATE`/`@DS_END_DATE` — 2 param này Looker Studio tự truyền vào dạng string `YYYYMMDD` theo date range control trên report, `PARSE_DATE('%Y%m%d', ...)` convert đúng sang DATE. Nếu chạy test standalone ngoài Looker Studio (BQ console/Python), thay 2 param này bằng `DATE('YYYY-MM-DD')` cụ thể. Đã test lại toàn bộ trên data thật (2026-06-01 → 2026-07-02, giờ VN): 507 dòng, đủ cột kể cả `user_country_code`/`product_type`. Nếu cần decode UTM đầy đủ mọi ký tự (không chỉ các mã phổ biến `%20`/`%2B`/`%28`/`%29`/`%26`), nên xử lý thêm ở layer BI/Python thay vì SQL.

### Định danh transaction (transaction ID)
Không có cột đơn lẻ nào unique theo transaction — `id` (và `pay_system_id`) là ID của **subscription**, lặp lại qua nhiều dòng webhook (920 subscription nhưng 2444 dòng trong bảng). Phải ghép **`(id, charges_count)`** — `charges_count` tăng dần mỗi lần charge thật → verify trên 482 dòng real-charge: 482 combo `(id, charges_count)` unique, không trùng.

### Timezone khi filter theo "ngày" — dùng `Asia/Ho_Chi_Minh`, không dùng UTC thô
`event_date` parse ra là UTC, nhưng Stripe Home dashboard hiển thị "Today"/số liệu theo **timezone account (giờ VN, UTC+7)**. Nếu filter `DATE(event_date) = 'YYYY-MM-DD'` (UTC thô) sẽ lệch với số Stripe hiển thị. Đã verify trên data thật ngày 2026-07-02: Stripe Home hiển thị "Successful payments: 96" — filter theo UTC ra 36 (Stripe) + 1 (PayPal) = 37, sai; filter đúng theo giờ VN ra **96**, khớp chính xác:

```sql
DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at), 'Asia/Ho_Chi_Minh') = '2026-07-02'
```

Lưu ý: `total_revenue`/Gross volume của Stripe Home **không cùng định nghĩa** với `SUM(amount_real)` — số này thường không khớp Gross volume của Stripe (ngay trong Stripe, Gross volume và Payments→Succeeded cũng đã lệch nhau ~35%). Nên đối chiếu với Stripe → Transactions → Payments → filter Succeeded cùng khung giờ, không đối chiếu với Gross volume ở Home.

### `status` trên dòng real-charge không phải luôn là `active` — race condition webhook, KHÔNG filter theo status
Trong tập real-charge (`event_type IN (...)`), phần lớn `status='active'` nhưng vẫn có vài dòng `incomplete`/`past_due` (verify lúc kiểm tra: 4 `incomplete` + 3 `past_due` trên 507 dòng, ~$330). Đã trace full timeline từng subscription: `charge.succeeded` luôn ghi lại **trước 1-7 giây** so với dòng `customer.subscription.updated` (status → `active`) — 2 webhook Stripe gửi gần như đồng thời nhưng thứ tự ingest không đảm bảo. Đây là race condition, không phải lỗi/hoàn tiền — tiền vẫn thu thật.
- `incomplete` + `charge.succeeded` = trial vừa convert sang paid lần đầu (charges_count=1), status chưa kịp cập nhật.
- `past_due` + `charge.succeeded` = renewal retry sau khi lần charge trước fail, retry thành công (charges_count≥2), status chưa kịp phục hồi về active.

**Không thêm `AND status = 'active'` vào query revenue** — sẽ vô tình loại bỏ nhầm các giao dịch thật này.

### Tính revenue: dùng `amount_real`, KHÔNG dùng `total_revenue`
- `amount_real` = số tiền của **riêng lần charge đó** → dùng `SUM(amount_real)` trên các dòng đã filter real-charge event để tính revenue theo transaction/period.
- `total_revenue` = tổng **lũy kế** của cả subscription tính đến thời điểm dòng đó, lặp lại giá trị trên mọi dòng của subscription → `SUM(total_revenue)` theo dòng sẽ bị đếm trùng nhiều lần. Chỉ dùng để xem LTV hiện tại của 1 subscription (lấy dòng mới nhất theo `updated_at`), không cộng dồn theo transaction.

### Phân loại `product_type` (subscription / onetime / other) — dùng `price_label`, KHÔNG dùng `plan_name`
`plan_name` là tên marketing tự do, không phải lúc nào cũng chứa từ khóa thời gian (`week`/`year`/`month`/`quarter`/`trial`) nên string-match trên `plan_name` sẽ bỏ sót. Đã verify trên data thật: rule dựa vào `plan_name` phân loại SAI 4/13 plan (`AI one`, `Calories_webfunnel`, `test local`, `test product` — tổng 68 dòng) thành `other` trong khi thực chất đều là `subscription` (theo `price_label` có `1 year`/`7 days`/`1 week`/`1 month`).

`price_label` là field system-generated (từ price object bên payment gateway) luôn chứa `Lifetime` (onetime) hoặc đơn vị thời gian (subscription) → đáng tin cậy hơn:

```sql
CASE
  WHEN REGEXP_CONTAINS(LOWER(price_label), r'lifetime') THEN 'onetime'
  WHEN REGEXP_CONTAINS(LOWER(price_label), r'day|week|month|year') THEN 'subscription'
  ELSE 'other'
END AS product_type
```

Đã test trên toàn bộ 13 giá trị `plan_name` hiện có — ra đúng 100% (0 dòng rơi vào `other`).

### Txn fail — KHÔNG có trong 2 bảng này
Không có event_type nào đại diện cho charge fail (không có `charge.failed`/`invoice.payment_failed`). Fail chỉ thể hiện gián tiếp qua `status='incomplete'` (fail lần đầu, 594 dòng) hoặc `status='past_due'` (fail renewal, 451 dòng) trên event `customer.subscription.created/updated`, và không có cột `decline_reason`. Nếu cần số liệu fail/decline reason khớp Stripe dashboard (Payments → Failed), phải lấy trực tiếp từ Stripe, không đủ trong 2 bảng raw này.

### Bảng chỉ ghi từ lúc webhook chạy — không có lịch sử trước đó
Pipeline dùng webhook nên chỉ bắt được event **từ lúc webhook bắt đầu chạy trở đi** (bảng `web2wave-raw` có data từ 2026-06-27), không backfill được các event xảy ra trước đó. Hệ quả: 1 subscription có thể xuất hiện lần đầu trong bảng ở `charges_count=2` (hoặc cao hơn) mà không có dòng `charges_count=1` — vì lần charge đầu tiên của nó xảy ra trước khi webhook được setup, không phải lỗi data. Verify: 84 id đang ở `charges_count>=2`, chỉ 66 có dòng `charges_count=1` trong bảng (18 id "mồ côi" P1 do giới hạn webhook).

### Tính retention subscription theo lần charge (`charges_count`) — mẫu số luôn cố định = P0
Định nghĩa (theo yêu cầu): `P0` = user có `charges_count=1` (lần charge đầu). `P1` = user đạt `charges_count=2`, `P2` = đạt `charges_count=3`... `RR_Pn = COUNT(DISTINCT id đạt charges_count >= n+1) / COUNT(DISTINCT id ở P0)` — **mẫu số luôn là P0**, không đổi theo từng bước (khác với step-retention P(n-1)→Pn). Tự sinh số period theo `MAX(charges_count)` thực tế trong data, không hardcode P1/P2/P3 thành cột riêng.

```sql
WITH charge_counts AS (
  SELECT id, plan_name, MAX(charges_count) AS max_reached
  FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
  WHERE event_type IN ('charge.succeeded', 'PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.SALE.COMPLETED')
    AND real_payment = 1
  GROUP BY id, plan_name
),
bounds AS (
  SELECT MAX(max_reached) - 1 AS top_p FROM charge_counts
),
curve AS (
  SELECT plan_name, p AS period, COUNT(DISTINCT id) AS cohort_count
  FROM charge_counts
  CROSS JOIN UNNEST(GENERATE_ARRAY(0, (SELECT top_p FROM bounds))) AS p
  WHERE max_reached >= p + 1     -- period P nghĩa là charges_count >= P+1
  GROUP BY plan_name, period
),
p0 AS (
  SELECT plan_name, cohort_count AS p0_count FROM curve WHERE period = 0
)
SELECT c.plan_name, c.period, c.cohort_count, p0.p0_count,
       ROUND(SAFE_DIVIDE(c.cohort_count, p0.p0_count) * 100, 1) AS retention_pct
FROM curve c JOIN p0 ON c.plan_name = p0.plan_name
ORDER BY c.plan_name, c.period
```

Dùng `MAX(charges_count)` per `id` (không join theo từng dòng) — vì `charges_count` là counter tuyệt đối từ gateway, cách này không bị ảnh hưởng bởi vấn đề "mồ côi P1" (id vẫn được tính đúng dù thiếu dòng P0 do giới hạn webhook).

**Cách dùng trong Looker Studio (không hardcode cột)**: dùng chart **Pivot Table** — Rows = `plan_name`, Columns = `period`, Metric = `retention_pct` (hoặc `cohort_count` nếu muốn số tuyệt đối).

Kết quả thật (2026-07-02): `1-WEEK PLAN` P1 = 71/357 = 19.9%, `4-WEEK PLAN` P1 = 2/53 = 3.8%, `Calories_webfunnel` P1 = 6/11 = 54.5%. Các plan khác chỉ có P0 (chưa ai lên P1) do data quá mới.

**Caveat quan trọng**: RR ≈ 0% của plan chu kỳ dài (yearly/quarterly) hiện tại **không phản ánh retention thật** — chỉ vì webhook mới chạy ~5 ngày (từ 27/06), chưa đủ 1 chu kỳ billing để bất kỳ ai renew. RR chỉ đáng tin ngay bây giờ với plan chu kỳ ngắn (`1-WEEK PLAN`, `4-WEEK PLAN`); numbers của plan dài sẽ tự populate khi data tích lũy đủ thời gian — không cần chỉnh logic query, chỉ cần đợi data.

### Thêm dim khác (country, utm_campaign, url_host, payment_system_label) — 1 bug đã gặp, cách tránh
Không hardcode nhiều dim vào 1 `GROUP BY` cứng — mẫu (n) sẽ quá nhỏ khi chia nhỏ theo nhiều chiều cùng lúc (data hiện tại chỉ ~509 user P0). Cách đúng: đưa mọi dim vào **base table ở mức `id`** (mỗi id 1 dòng kèm sẵn thuộc tính), để Looker Studio Pivot Table tự chọn breakdown theo dim nào cần xem mà không cần sửa SQL.

**Bug đã gặp khi làm việc này**: lúc đầu lấy country/campaign bằng cách tách riêng 1 CTE `WHERE charges_count = 1` rồi JOIN với `MAX(charges_count)` — ra **0% ở MỌI country**, trông như bug data nhưng thực ra là bug logic: lọc `charges_count=1` tự động chỉ chọn đúng nhóm **vừa mới charge lần đầu, chưa ai kịp renew** (vì data quá mới), nên retention luôn ra 0 bất kể dim gì. Cách đúng — lấy tất cả dim bằng `ANY_VALUE(...)` trong **cùng 1 lần `GROUP BY id`** với `MAX(charges_count)` (không tách CTE riêng theo charges_count cụ thể), vì các dim này ổn định (không đổi) qua mọi lần charge của cùng 1 `id` — đã verify: `url`/`utm_campaign`/`user_country_code`/`payment_system_label` giống nhau trên mọi dòng charge (kể cả renewal) của cùng 1 `id`.

```sql
WITH id_base AS (
  SELECT
    id,
    MAX(charges_count) AS max_reached,
    ANY_VALUE(plan_name) AS plan_name,
    ANY_VALUE(payment_system_label) AS payment_system_label,
    ANY_VALUE(user_country_code) AS user_country_code,
    ANY_VALUE(NET.HOST(url)) AS url_host,
    ANY_VALUE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
      REGEXP_EXTRACT(url, r'[?&]utm_campaign=([^&]*)'),
      '%20',' '),'%2B','+'),'%28','('),'%29',')'),'%26','&')) AS utm_campaign
  FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
  WHERE event_type IN ('charge.succeeded', 'PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.SALE.COMPLETED')
    AND real_payment = 1
  GROUP BY id
),
bounds AS (SELECT MAX(max_reached) - 1 AS top_p FROM id_base)
SELECT
  id_base.*,
  p AS period,
  IF(max_reached >= p + 1, 1, 0) AS retained
FROM id_base
CROSS JOIN UNNEST(GENERATE_ARRAY(0, (SELECT top_p FROM bounds))) AS p
```

Verify trên data thật: retention P1 theo `user_country_code` ra số hợp lý (US 9.1%, AU 13.9%, GB 13.0%, NZ 26.7%...), khác hẳn kết quả sai (0% mọi nơi) trước khi fix.

### Thêm `event_date` (ngày cohort) + filter theo Date Range control
Thêm `MIN(event_date)` per `id` vào `id_base` = ngày cohort/install (ngày sớm nhất có transaction thành công ghi nhận được cho `id` đó), rồi filter theo `@DS_START_DATE`/`@DS_END_DATE` như query transaction — nhưng ý nghĩa `event_date` ở đây **khác** query transaction: đây là ngày cohort của USER, không phải ngày của TỪNG transaction riêng lẻ.

```sql
WITH id_base AS (
  SELECT
    id,
    MIN(DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at), 'Asia/Ho_Chi_Minh')) AS event_date,
    MAX(charges_count) AS max_reached,
    ANY_VALUE(plan_name) AS plan_name,
    ANY_VALUE(payment_system_label) AS payment_system_label,
    ANY_VALUE(user_country_code) AS user_country_code,
    ANY_VALUE(NET.HOST(url)) AS url_host,
    ANY_VALUE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
      REGEXP_EXTRACT(url, r'[?&]utm_campaign=([^&]*)'),
      '%20',' '),'%2B','+'),'%28','('),'%29',')'),'%26','&')) AS utm_campaign,
    ANY_VALUE(
      CASE
        WHEN REGEXP_CONTAINS(LOWER(price_label), r'lifetime') THEN 'onetime'
        WHEN REGEXP_CONTAINS(LOWER(price_label), r'day|week|month|year') THEN 'subscription'
        ELSE 'other'
      END
    ) AS product_type
  FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
  WHERE event_type IN ('charge.succeeded', 'PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.SALE.COMPLETED')
    AND real_payment = 1
  GROUP BY id
  HAVING MIN(charges_count) = 1   -- QUAN TRỌNG: loại id "mồ côi P0" — xem bug bên dưới
),
bounds AS (SELECT MAX(max_reached) - 1 AS top_p FROM id_base)  -- tính trên TOÀN BỘ id_base trước khi filter ngày, để số cột period không co giãn khi đổi date range
SELECT
  id_base.*,
  p AS period,
  IF(max_reached >= p + 1, 1, 0) AS retained
FROM id_base
CROSS JOIN UNNEST(GENERATE_ARRAY(0, (SELECT top_p FROM bounds))) AS p
WHERE 1=1
  AND event_date BETWEEN PARSE_DATE('%Y%m%d', @DS_START_DATE) AND PARSE_DATE('%Y%m%d', @DS_END_DATE)
```

**Bug đã gặp trên dashboard thật — id "mồ côi P0" làm sai lệch cả cohort_date lẫn P1**: Pivot table filter theo `event_date` = 1/7 (Jul 1), plan `1-WEEK PLAN` ra P0=78, P1=17 (22%) — nhìn tưởng hợp lý ("78 user mua, 17 renew ngay") nhưng SAI. Verify: đúng 61/78 id có `MIN(charges_count)=1` (mua lần đầu thật vào 1/7), còn **17/78 id có `MIN(charges_count)=2`** — tức lần charge sớm nhất bắt được của họ trong bảng đã là **renewal** (họ subscribe từ trước 27/06, trước khi webhook chạy), không phải mua mới ngày 1/7. Vì `event_date = MIN(ngày có real-charge)` gắn nhầm ngày renewal này thành "ngày cohort", nên 17 id này bị tính vào CẢ mẫu số (P0) VÀ tử số (P1) của cùng 1 ngày → tạo cảm giác giả "renew ngay trong ngày mua". Check thêm bằng cách so `first_ts` (ngày cohort) và `second_ts` (ngày đạt charges_count=2): cả 17 case đều `first_ts = second_ts` (cùng 1 dòng), xác nhận đây chỉ là 1 charge duy nhất bị hiểu nhầm thành cả P0 và P1.

**Sau khi fix (`HAVING MIN(charges_count) = 1`)**: P0 = 61, P1 = 0 (0%) — đúng thực tế vì gói weekly mới qua 1 ngày (chưa đủ 1 chu kỳ để renew).

**Hệ quả của fix**: id mồ côi bị loại hoàn toàn khỏi bảng retention theo cohort_date (không gán được ngày cohort đúng cho họ) — khác với bảng retention theo `charges_count` thuần (không quan tâm ngày, ở mục trên) vẫn giữ được id mồ côi vì không cần biết ngày P0 chính xác.

**`product_type` (subscription/onetime)**: dùng `ANY_VALUE(...)` trên `price_label` giống các dim khác — đã verify **0 id** có `price_label` khác nhau qua các lần charge, nên lấy `ANY_VALUE` an toàn (không cần lo lệch giữa lần đầu và renewal). Test trên data thật: 884 dòng `subscription`, 138 dòng `onetime`, không có `other`.

### Bảng thống kê user mồ côi P0 (bị loại khỏi bảng retention theo cohort_date)
Query ngược lại với `id_base` — đổi `HAVING MIN(charges_count) = 1` thành `> 1` — để theo dõi riêng nhóm bị loại, xem quy mô lớn/nhỏ ra sao và có giảm dần theo thời gian không (nếu giảm về 0 nghĩa là data "sạch" dần, hết mồ côi).

```sql
SELECT
  id,
  MIN(DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at), 'Asia/Ho_Chi_Minh')) AS first_seen_date,  -- ngày bắt được sớm nhất, KHÔNG phải ngày mua thật
  MIN(charges_count) AS min_charge,   -- charges_count tại lần đầu bắt được — luôn >=2 với nhóm này
  MAX(charges_count) AS max_reached,
  ANY_VALUE(plan_name) AS plan_name,
  ANY_VALUE(payment_system_label) AS payment_system_label,
  ANY_VALUE(user_country_code) AS user_country_code,
  ANY_VALUE(NET.HOST(url)) AS url_host,
  ANY_VALUE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
    REGEXP_EXTRACT(url, r'[?&]utm_campaign=([^&]*)'),
    '%20',' '),'%2B','+'),'%28','('),'%29',')'),'%26','&')) AS utm_campaign,
  ANY_VALUE(
    CASE
      WHEN REGEXP_CONTAINS(LOWER(price_label), r'lifetime') THEN 'onetime'
      WHEN REGEXP_CONTAINS(LOWER(price_label), r'day|week|month|year') THEN 'subscription'
      ELSE 'other'
    END
  ) AS product_type
FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
WHERE event_type IN ('charge.succeeded', 'PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.SALE.COMPLETED')
  AND real_payment = 1
GROUP BY id
HAVING MIN(charges_count) > 1
```

Kết quả thật (2026-07-02): **82 id mồ côi**, 100% có `min_charge = 2` (chưa ai mồ côi từ charge thứ 3+). Theo plan: `1-WEEK PLAN` 73, `Calories_webfunnel` 7, `4-WEEK PLAN` 2. Theo `first_seen_date`: rải đều 28/06→02/07 (16, 15, 7, 19, 25) — hợp lý vì đây là user cũ (subscribe trước 27/06), renew rải theo ngày.

**Dùng trong Looker Studio**: add làm data source thứ 3, dựng Pivot Table hoặc Bar chart — Row = `plan_name`/`first_seen_date`, Metric = `Record Count`.

### Setup trong Looker Studio
1. **Add data source**: `Resource → Manage added data sources → Add → BigQuery → CUSTOM QUERY`, paste query `id_base`/`period` ở trên, project `ikame-apps-dev`.
2. Đổi field type: `period` = Number (dimension), `retained` = Number (metric).
3. `Insert → Pivot Table`: Row = dim muốn xem (`user_country_code`/`plan_name`/`utm_campaign`/`url_host`/`payment_system_label`), Column = `period`, Metric = `retained` (đổi aggregation Sum → **Average**), Style → format Percent.
4. Thêm `Insert → Control → Drop-down list` cho các dim còn lại để filter.
5. **Nâng cao — 1 chart đổi được breakdown dim**: tạo Parameter `p_breakdown_dim` (Text, allowed values: Country/Plan/Campaign/URL host/Gateway) → tạo Calculated field `breakdown_dim = CASE WHEN p_breakdown_dim="Country" THEN user_country_code WHEN ...="Plan" THEN plan_name WHEN ...="Campaign" THEN utm_campaign WHEN ...="URL host" THEN url_host WHEN ...="Gateway" THEN payment_system_label END` → dùng `breakdown_dim` làm Row dimension, thêm Parameter control (drop-down) lên trang để user tự đổi.

### Retention curve kiểu cohort-by-day (rows=install date/plan, columns=period elapsed) — dùng Pivot Table, không hardcode cột
Khác với cách tính theo `charges_count` ở trên (đo "đã renew tới lần thứ mấy"), đây là kiểu retention chuẩn app-analytics: "subscription này còn sống (chưa churn) sau N ngày kể từ lần charge đầu?" — cần thêm event churn (`customer.subscription.deleted`/`BILLING.SUBSCRIPTION.CANCELLED`) mà query revenue không có sẵn.

**Cách không hardcode cột period**: xuất data ở dạng long-format (`id × period_number × retained flag`), rồi dùng chart **Pivot Table** trong Looker Studio — Rows = `plan_name` hoặc `cohort_date`, Columns = `period_number` (tự sinh cột theo data, không cần khai báo trước), Metric = `retained` aggregation **Average**. Period nào chưa đủ ngày (`cohort_date + N > hôm nay`) thì KHÔNG xuất dòng — pivot table tự hiện trống, đúng ý nghĩa "chưa đủ dữ liệu" chứ không phải "0%".

```sql
WITH cohort AS (
  SELECT id, plan_name,
         MIN(DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at), 'Asia/Ho_Chi_Minh')) AS cohort_date
  FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
  WHERE event_type IN ('charge.succeeded','PAYMENT.CAPTURE.COMPLETED','PAYMENT.SALE.COMPLETED')
    AND real_payment = 1 AND charges_count = 1
  GROUP BY id, plan_name
),
churn AS (
  SELECT id,
         MIN(DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at), 'Asia/Ho_Chi_Minh')) AS churn_date
  FROM `ikame-apps-dev.tracking_transaction_providers.web2wave-raw`
  WHERE event_type IN ('customer.subscription.deleted','BILLING.SUBSCRIPTION.CANCELLED')
  GROUP BY id
),
base AS (
  SELECT cohort.id, cohort.plan_name, cohort.cohort_date, churn.churn_date
  FROM cohort LEFT JOIN churn USING(id)
)
SELECT
  base.id, base.plan_name, base.cohort_date,
  p AS period_number,
  IF(base.churn_date IS NULL OR base.churn_date > DATE_ADD(base.cohort_date, INTERVAL p DAY), 1, 0) AS retained
FROM base, UNNEST(GENERATE_ARRAY(0, 30)) AS p   -- cap tạm 30 ngày, tăng khi data dài ra
WHERE DATE_ADD(base.cohort_date, INTERVAL p DAY) <= CURRENT_DATE('Asia/Ho_Chi_Minh')
```

**Đã test trên data thật (2026-07-02)**: ra gần như 100% ở mọi period — **không phải retention tốt**, mà vì toàn bộ bảng hiện chỉ có **1 event churn duy nhất** (data quá mới, webhook chạy 5 ngày, cohort sớm nhất 2026-06-28, period tối đa quan sát được = 4 ngày). Số liệu sẽ phản ánh đúng dần khi tích lũy thêm thời gian và churn event xảy ra tự nhiên.
