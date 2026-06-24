# note -- revenue-discrepancy-ga4-vs-adjust

## Findings

### 2026-06-24 — Root cause chênh lệch GA4 vs Adjust (iOS Face Scanner)

**Kết luận: KHÔNG có bug, không có mất revenue thực sự.**

#### 1. `in_app_purchase` trên GA4 = $0 revenue — đúng

- App chỉ có 1 event `in_app_purchase`, trigger khi user mua `facescan_week_trial_6.99_226`
- Đây là **trial start** → không có charge → revenue = $0
- Tương đương trên Adjust là event `trial started` — cũng không có revenue
- → GA4 và Adjust khớp nhau ở điểm này ✓

#### 2. Revenue $127.08 + $7.56 trên GA4 từ đâu?

Revenue $142.20 tuần Jun 17-23 đến từ 2 event S2S (server-to-server giữa Apple và Firebase):

| Event | Revenue | Ghi chú |
|-------|---------|---------|
| `app_store_subscription_renew` | $127.08 | 15 renewals |
| `app_store_subscription_convert` | $7.56 | 1 convert (sandbox, không tính) |
| `in_app_purchase` | $7.56 | Jun 22/23, nghi sandbox |

- **Nghi vấn**: các event S2S này xảy ra **trước thời điểm Adjust init thành công** → Adjust không nhận được
- Event $7.56 ngày 23/06 từ `app_store_subscription_convert` là **sandbox** → không tính vào revenue thực

#### 3. Tại sao Adjust = $0?

- Adjust không nhận S2S notification từ Apple (chưa setup Apple S2S forwarding sang Adjust)
- Hoặc Adjust chưa init thành công vào thời điểm các renewal/convert diễn ra
- → Adjust chỉ track được event do SDK client gửi, không track được server-side subscription event

#### Summary

```
GA4 Console $142.20  ← app_store_subscription_renew (trước khi Adjust init)
                       + sandbox events (không tính)
Adjust $0            ← chưa nhận S2S subscription events từ Apple
in_app_purchase      ← trial start, $0 revenue — đúng trên cả 2 platform
```

**Không có discrepancy thực sự** — chỉ là Adjust chưa được setup nhận Apple S2S subscription callbacks.

## Queries

```sql
-- Revenue events trong intraday tables
SELECT event_date, event_name, COUNT(*) AS cnt,
  SUM(COALESCE(
    (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value'),
    (SELECT value.float_value  FROM UNNEST(event_params) WHERE key = 'value'), 0
  )) AS sum_value
FROM `ios-face-scanner.analytics_540983063.events_intraday_*`
WHERE event_name IN ('app_store_subscription_renew','app_store_subscription_convert','in_app_purchase')
GROUP BY 1, 2 ORDER BY 1, 2

-- NOTE: app_store_subscription_renew/convert chỉ có trong finalized tables (events_YYYYMMDD)
-- Intraday tables chưa có vì BQ export mới connect từ Jun 11/2026
```
