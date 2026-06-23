# Note — Phân tách luồng intro6 (3.3.5) vs intro7 (3.3.7)

> App iOS Heart Rate (iKame) — luồng intro theo version & traffic source.
> Cập nhật: 2026-06-10

---

## 1. Filter cố định (áp dụng mọi query)

```sql
traffic_source_medium = 'FacebookW2A'
AND session_number    = 1
AND country           = 'United States'
AND version IN ('3.3.5','3.3.7')
AND (
  (version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')  -- 17 ngày
  OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24') -- 17 ngày
)
```

- **Bảng**: `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
- Bảng dạng **flow transition**: mỗi dòng là 1 bước chuyển `screen_from → screen_to`, sắp theo `event_timestamp` (tie-break: `flow_row_number`, `event_row_in_flow`).
- **Version lấy từ cột `version`** (thuộc tính bản app, có trên MỌI event) — KHÔNG suy từ tên màn. Tên màn chỉ dùng để biết user đi sâu tới đâu.

---

## 2. Cách tách luồng (signature theo tên màn)

Mỗi `user_pseudo_id` chỉ thuộc 1 version & 1 luồng. Các màn **chỉ xuất hiện ở 1 version** (đã verify, 0 lẫn chéo):

| Version | Chữ ký intro | Chữ ký subscribe | Khác (only) |
|---------|--------------|------------------|-------------|
| **3.3.5** | `intro6*` | `subscribe5` | `membership_benefits`, `subscribe_content` |
| **3.3.7** | `intro7*` | `subscribe5_new` | — |

- Đã kiểm tra: **không user nào chạm cả intro6 lẫn intro7** (both = 0).
- `onboarding_5_video*` và `intro2*` xuất hiện ở **cả 2 version** (nhỏ) → KHÔNG phải chữ ký riêng.

### Quy tắc nhận diện luồng (tốt nhất = kết hợp intro HOẶC subscribe)
- Dùng riêng `intro6/intro7`: bắt user vào intro nhưng **bỏ sót** user nhảy thẳng subscribe (mất event intro).
- Dùng riêng `subscribe5/_new`: nằm sâu hơn → **bỏ sót** user drop trong lúc xem intro.
- **Kết hợp `intro OR subscribe`** = vét đầy đủ nhất → luồng chính ~94.6%.

---

## 3. Kết quả

### 3.1. Phân loại theo luồng — chỉ dùng intro

| Version | Luồng | Users | Tỷ trọng |
|---------|-------|------:|---------:|
| 3.3.5 | Luồng intro6 | 17,879 | 93.64% |
| 3.3.5 | Không vào intro nào | 1,172 | 6.14% |
| 3.3.5 | intro2 (cũ) | 42 | 0.22% |
| 3.3.7 | Luồng intro7 | 15,870 | 93.12% |
| 3.3.7 | Không vào intro nào | 1,005 | 5.90% |
| 3.3.7 | onboarding_5_video | 162 | 0.95% |
| 3.3.7 | intro2 (cũ) | 5 | 0.03% |

### 3.2. Phân loại theo luồng — KẾT HỢP (intro HOẶC subscribe) ✅ khuyến nghị

| Version | Luồng | Users | Tỷ trọng |
|---------|-------|------:|---------:|
| 3.3.5 | **Luồng intro6** (intro6 OR subscribe5) | **18,079** | **94.69%** |
| 3.3.5 | Không vào luồng nào | 1,010 | 5.29% |
| 3.3.5 | intro2 (cũ) | 4 | 0.02% |
| 3.3.7 | **Luồng intro7** (intro7 OR subscribe5_new) | **16,119** | **94.58%** |
| 3.3.7 | Không vào luồng nào | 915 | 5.37% |
| 3.3.7 | onboarding_5_video | 5 | 0.03% |
| 3.3.7 | intro2 (cũ) | 3 | 0.02% |

So sánh: kết hợp vét thêm **+200 user (3.3.5)**, **+249 user (3.3.7)** so với chỉ dùng intro.

### 3.3. Phân bố theo bước sâu nhất đạt được (deepest stage)

| Bước sâu nhất | 3.3.5 | % | 3.3.7 | % |
|---------------|------:|---:|------:|---:|
| Splash only | 344 | 1.80% | 187 | 1.10% |
| Sign-in only | 638 | 3.34% | 722 | 4.24% |
| Intro | 1,482 | 7.76% | 2,258 | 13.25% |
| Subscribe | 10,407 | 54.51% | 9,544 | 56.00% |
| Home | 73 | 0.38% | 2,200 | 12.91% |
| Measure | 2,914 | 15.26% | 349 | 2.05% |
| Measure Result | 3,235 | 16.94% | 1,782 | 10.46% |
| **Tổng** | **19,093** | 100% | **17,042** | 100% |

⚠️ **Cần điều tra**: cặp Home ↔ Measure bị "đảo" giữa 2 version (3.3.5: Home 0.38% / Measure 15.26%; 3.3.7: Home 12.91% / Measure 2.05%) → nghi định nghĩa/thứ tự màn home vs measure khác nhau giữa intro6 và intro7. Chuẩn hóa trước khi so sánh phần sau Subscribe.

---

## 4. Query đã test

### 4.1. Phân loại luồng — kết hợp intro HOẶC subscribe (khuyến nghị)

```sql
WITH ev AS (
  SELECT version, user_pseudo_id, screen_from AS sf, screen_to AS st
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium = 'FacebookW2A'
    AND session_number = 1
    AND country = 'United States'
    AND version IN ('3.3.5','3.3.7')
    AND (
      (version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24')
    )
),
u AS (
  SELECT version, user_pseudo_id,
    MAX(IF(sf LIKE 'intro6%' OR st LIKE 'intro6%',1,0))           AS i6,
    MAX(IF(sf LIKE 'intro7%' OR st LIKE 'intro7%',1,0))           AS i7,
    MAX(IF(sf = 'subscribe5'     OR st = 'subscribe5',1,0))       AS sub5,
    MAX(IF(sf = 'subscribe5_new' OR st = 'subscribe5_new',1,0))   AS sub5new,
    MAX(IF(sf LIKE 'intro2%' OR st LIKE 'intro2%',1,0))           AS i2,
    MAX(IF(sf LIKE 'onboarding_5_video%' OR st LIKE 'onboarding_5_video%',1,0)) AS vid
  FROM ev
  GROUP BY version, user_pseudo_id
),
cls AS (
  SELECT version,
    CASE
      WHEN i6=1 OR sub5=1    THEN 'Luong intro6'
      WHEN i7=1 OR sub5new=1 THEN 'Luong intro7'
      WHEN i2=1              THEN 'Luong intro2 (cu)'
      WHEN vid=1             THEN 'Luong onboarding_5_video'
      ELSE 'Khong vao luong nao'
    END AS flow
  FROM u
)
SELECT version, flow, COUNT(*) AS users,
  ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY version),2) AS pct
FROM cls
GROUP BY version, flow
ORDER BY version, users DESC;
```

### 4.2. Phân bố theo bước sâu nhất (deepest stage)

```sql
WITH ev AS (
  SELECT version, user_pseudo_id, screen_from AS sf, screen_to AS st
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium = 'FacebookW2A'
    AND session_number = 1
    AND country = 'United States'
    AND version IN ('3.3.5','3.3.7')
    AND (
      (version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24')
    )
),
u AS (
  SELECT version, user_pseudo_id,
    MAX(IF(sf='measure_result2' OR st='measure_result2',1,0)) AS r_result,
    MAX(IF(sf='measure' OR st='measure',1,0))                 AS r_measure,
    MAX(IF(sf='home' OR st='home',1,0))                       AS r_home,
    MAX(IF(sf LIKE 'subscribe5%' OR st LIKE 'subscribe5%',1,0)) AS r_sub,
    MAX(IF(sf LIKE 'intro6%' OR st LIKE 'intro6%'
        OR sf LIKE 'intro7%' OR st LIKE 'intro7%',1,0))       AS r_intro,
    MAX(IF(sf='sign_in_onboarding' OR st='sign_in_onboarding',1,0)) AS r_signin,
    MAX(IF(sf='splash' OR st='splash',1,0))                   AS r_splash
  FROM ev
  GROUP BY version, user_pseudo_id
),
bucket AS (
  SELECT version,
    CASE
      WHEN r_result=1  THEN '7. Measure Result'
      WHEN r_measure=1 THEN '6. Measure'
      WHEN r_home=1    THEN '5. Home'
      WHEN r_sub=1     THEN '4. Subscribe'
      WHEN r_intro=1   THEN '3. Intro'
      WHEN r_signin=1  THEN '2. Sign-in only'
      WHEN r_splash=1  THEN '1. Splash only'
      ELSE '0. Other/undefined'
    END AS stage
  FROM u
)
SELECT version, stage, COUNT(*) AS users,
  ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY version),2) AS pct
FROM bucket
GROUP BY version, stage
ORDER BY version, stage;
```

### 4.3. Liệt kê chuỗi luồng theo N màn đầu (đổi `rn <= N`)

```sql
WITH base AS (
  SELECT user_pseudo_id, version, screen_from,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id
                       ORDER BY event_timestamp, flow_row_number, event_row_in_flow) AS rn
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium = 'FacebookW2A'
    AND session_number = 1
    AND country = 'United States'
    AND version IN ('3.3.5','3.3.7')
    AND (
      (version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24')
    )
),
flows AS (
  SELECT user_pseudo_id, version,
    STRING_AGG(screen_from, ' > ' ORDER BY rn) AS flow
  FROM base WHERE rn <= 7   -- đổi 5/7/... tùy số màn cần xem
  GROUP BY user_pseudo_id, version
)
SELECT version, flow, COUNT(*) AS users,
  ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY version),2) AS pct
FROM flows
GROUP BY version, flow
ORDER BY version, users DESC;
```

### 4.4. Gắn nhãn từng user — `version - luồng` (1 dòng/user)

Dùng để export danh sách user kèm nhãn luồng (join sang phân tích khác). Nhãn dùng chữ ký kết hợp `intro OR subscribe`.

```sql
WITH ev AS (
  SELECT version, user_pseudo_id, screen_from AS sf, screen_to AS st
  FROM `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE`
  WHERE traffic_source_medium = 'FacebookW2A'
    AND session_number = 1
    AND country = 'United States'
    AND version IN ('3.3.5','3.3.7')
    AND (
      (version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
      OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24')
    )
),
u AS (
  SELECT version, user_pseudo_id,
    MAX(IF(sf LIKE 'intro6%' OR st LIKE 'intro6%',1,0))         AS i6,
    MAX(IF(sf LIKE 'intro7%' OR st LIKE 'intro7%',1,0))         AS i7,
    MAX(IF(sf = 'subscribe5'     OR st = 'subscribe5',1,0))     AS sub5,
    MAX(IF(sf = 'subscribe5_new' OR st = 'subscribe5_new',1,0)) AS sub5new,
    MAX(IF(sf LIKE 'intro2%' OR st LIKE 'intro2%',1,0))         AS i2,
    MAX(IF(sf LIKE 'onboarding_5_video%' OR st LIKE 'onboarding_5_video%',1,0)) AS vid
  FROM ev
  GROUP BY version, user_pseudo_id
)
SELECT
  user_pseudo_id,
  version,
  version || ' - ' || CASE
    WHEN i6=1 OR sub5=1    THEN 'intro6'
    WHEN i7=1 OR sub5new=1 THEN 'intro7'
    WHEN i2=1              THEN 'intro2 (cu)'
    WHEN vid=1             THEN 'onboarding_5_video'
    ELSE 'khong vao luong nao'
  END AS label
FROM u;
-- Muốn đếm theo nhãn: bọc ngoài `SELECT label, COUNT(*) ... GROUP BY label`
```

**Kết quả gắn nhãn (đã chạy):**

| Label | Users |
|-------|------:|
| 3.3.5 - intro6 | 18,079 |
| 3.3.5 - khong vao luong nao | 1,010 |
| 3.3.5 - intro2 (cu) | 4 |
| 3.3.7 - intro7 | 16,122 |
| 3.3.7 - khong vao luong nao | 912 |
| 3.3.7 - onboarding_5_video | 5 |
| 3.3.7 - intro2 (cu) | 3 |

#### Phân rã nhóm "khong vao luong nao" (rớt sớm, chưa tới intro)

| Dừng tại | 3.3.5 | 3.3.7 |
|----------|------:|------:|
| Splash (mở app rồi thoát) | 344 | 186 |
| Sign-in (đăng nhập xong rồi bỏ) | 634 | 713 |
| Nhảy thẳng Home/Measure (bỏ qua intro+subscribe) | 30 | 13 |

→ 3.3.7 drop ở Sign-in cao hơn (713 vs 634) — bản mới mất user nhiều hơn ngay chặng trước intro.
