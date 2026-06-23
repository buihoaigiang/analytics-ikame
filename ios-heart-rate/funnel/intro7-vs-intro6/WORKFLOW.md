# WORKFLOW — Phân tích & so sánh funnel intro (3.3.5 vs 3.3.7)

> Đọc file này TRƯỚC khi bắt tay vào task funnel/chart. Kết quả số chi tiết + query mẫu xem thêm [note.md](note.md).

---

## Mục tiêu
So sánh luồng intro app iOS Heart Rate giữa **3.3.5 (intro6)** và **3.3.7 (intro7)**: tỷ lệ chuyển đổi, drop-off từng màn, theo cùng cửa sổ 17 ngày.

---

## Các bước đã làm (workflow)

1. **Kết nối BigQuery** bằng Python `google.cloud.bigquery` (bq CLI lỗi). Credential qua env var.
2. **Khám phá schema** bảng `SCREEN_ACTIVE_AUDIENCE` → xác định dạng flow transition (`screen_from → screen_to`).
3. **Xác định luồng mỗi user**: lấy chuỗi `screen_from` theo `event_timestamp` (5 rồi 7 màn đầu) → thấy mỗi version có 1 luồng chủ đạo (~90%).
4. **Tìm chữ ký màn theo version** (màn chỉ xuất hiện ở 1 version): 3.3.5 = `intro6*`/`subscribe5`; 3.3.7 = `intro7*`/`subscribe5_new`. Verify **0 user lẫn intro6↔intro7**.
5. **Gom luồng nhỏ về luồng chính** bằng chữ ký kết hợp **`intro OR subscribe`** (vét cả user nhảy thẳng subscribe). Gán nhãn `version - luồng`.
6. **Dựng funnel Splash → Measure (đầu tiên)**: chuỗi `screen_from`, cắt tại lần đầu `screen_from='measure'`; ai không tới measure thì giữ hết session 1. Metric = **% distinct `user_pseudo_id`** mỗi màn (splash=100%).
7. **Vẽ chart so sánh** back-to-back 2 version ([build_funnel_compare.py](build_funnel_compare.py)) — align theo nhóm chức năng, bảng `vs %remain` + `vs %drop vs prev step`, gạch vàng phân tách 5 nhóm.
8. **Gom 5 nhóm chức năng & kết luận**: nghẽn lớn nhất là **paywall→home (~−53pp, cả 2 bản như nhau)**; 3.3.7 hao hụt hơn ở intro dài + select_*; bước home→measure khác biệt lớn nhưng **nghi đảo định nghĩa → chưa kết luận**.

---

## Filter cố định (mọi query)
```sql
traffic_source_medium = 'FacebookW2A' AND session_number = 1 AND country = 'United States'
AND version IN ('3.3.5','3.3.7')
AND ((version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
  OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24'))
```

---

## Query chính — Funnel Splash → Measure đầu tiên (% distinct user/màn)
```sql
WITH base AS (
  SELECT version, user_pseudo_id, screen_from,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id
                       ORDER BY event_timestamp, flow_row_number, event_row_in_flow) rn
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium='FacebookW2A' AND session_number=1 AND country='United States'
    AND version IN ('3.3.5','3.3.7')
    AND ((version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24'))
),
fm AS (  -- lan dau cham man measure cua moi user
  SELECT user_pseudo_id, MIN(rn) first_measure_rn
  FROM base WHERE screen_from='measure' GROUP BY user_pseudo_id
),
trunc AS (  -- cat tai measure dau tien; ai khong toi measure -> giu het
  SELECT b.version, b.user_pseudo_id, b.screen_from
  FROM base b LEFT JOIN fm USING(user_pseudo_id)
  WHERE fm.first_measure_rn IS NULL OR b.rn <= fm.first_measure_rn
),
tot AS (SELECT version, COUNT(DISTINCT user_pseudo_id) total FROM base GROUP BY version)
SELECT t.version, t.screen_from,
  COUNT(DISTINCT t.user_pseudo_id) users,
  ROUND(100*COUNT(DISTINCT t.user_pseudo_id)/MAX(tot.total),2) pct
FROM trunc t JOIN tot ON t.version=tot.version
GROUP BY t.version, t.screen_from
ORDER BY t.version, users DESC;
```

---

## Query phụ — Gán nhãn `version - luồng` (1 dòng/user)
```sql
WITH ev AS (
  SELECT version, user_pseudo_id, screen_from sf, screen_to st
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium='FacebookW2A' AND session_number=1 AND country='United States'
    AND version IN ('3.3.5','3.3.7')
    AND ((version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24'))
),
u AS (
  SELECT version, user_pseudo_id,
    MAX(IF(sf LIKE 'intro6%' OR st LIKE 'intro6%',1,0)) i6,
    MAX(IF(sf LIKE 'intro7%' OR st LIKE 'intro7%',1,0)) i7,
    MAX(IF(sf='subscribe5' OR st='subscribe5',1,0)) sub5,
    MAX(IF(sf='subscribe5_new' OR st='subscribe5_new',1,0)) sub5new
  FROM ev GROUP BY version, user_pseudo_id
)
SELECT user_pseudo_id, version,
  version || ' - ' || CASE
    WHEN i6=1 OR sub5=1    THEN 'intro6'
    WHEN i7=1 OR sub5new=1 THEN 'intro7'
    ELSE 'khong vao luong nao' END AS label
FROM u;
```

---

## Chart chính
[build_funnel_compare.py](build_funnel_compare.py) → [funnel_compare_335_337.html](funnel_compare_335_337.html)
- Back-to-back 2 phễu quay vào nhau, giữ nguyên tên màn mỗi version.
- Bảng phải: `vs %remain` + `vs %drop vs prev step (& ΔΔ)`, conditional formatting xanh→đỏ (chỉ tính tới hết subscribe).
- Gạch ngang **vàng** phân tách 5 nhóm chức năng.
- Chỉ xuất HTML; muốn verify thì render PNG tạm rồi xoá.
