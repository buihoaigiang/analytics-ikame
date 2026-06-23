# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ Đọc trước khi làm
Trước mọi task funnel/chart, **đọc [WORKFLOW.md](WORKFLOW.md)** (tóm tắt các bước làm + query chính đã test) và [note.md](note.md) (kết quả số chi tiết).

---

## Ngôn ngữ
Luôn trả lời bằng **tiếng Việt**.

---

## Mô tả dự án
Phân tích luồng intro của app **iOS Heart Rate** (iKame), theo hành trình:
**Splash →(các step khác nữa... sau đây là step chính thôi) Sign-in → Intro → Subscribe (IAP) → Home → Measure → Measure Result**

Mục tiêu: đo tỷ lệ chuyển đổi, drop-off rate và thời gian giữa các bước theo từng version và traffic source.

---

## Phiên bản so sánh

| Version | Thời gian | Số ngày |
|---------|-----------|---------|
| **3.3.7** | 25/05/2026 → 10/06/2026 | 17 ngày |
| **3.3.5** | 08/05/2026 → 24/05/2026 | 17 ngày |

Luôn so sánh song song cùng số ngày để đảm bảo tính công bằng.

credential lấy ở file C:\Users\admin\Desktop\20260610\gcloud_credentials.json

---

## BigQuery
- **Project**: `team-begamob`
- **Bảng chính**: `team-begamob.iOS_Heart_Rate_CACHED_Events_08.SCREEN_ACTIVE_AUDIENCE` (~35.6M rows)
- **Filter cố định**: `traffic_source_medium = 'FacebookW2A'`, `session_number = 1`, `country = 'United States'`
- **Date window** (gắn theo version để so sánh công bằng 17 ngày):
  ```sql
  (version='3.3.7' AND event_date BETWEEN '2026-05-25' AND '2026-06-10')
  OR (version='3.3.5' AND event_date BETWEEN '2026-05-08' AND '2026-05-24')
  ```
- **Quy tắc**: Chạy query thật trước, chỉ trả syntax sau khi query thành công.

---

## Cách chạy query (tooling)
- `bq` CLI bị lỗi import trên máy này → **dùng Python `google.cloud.bigquery`**.
- Set credential qua env var, KHÔNG hardcode:
  ```python
  import os
  from google.cloud import bigquery
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\admin\Desktop\20260610\gcloud_credentials.json'
  client = bigquery.Client(project='team-begamob')
  ```
- **Bẫy encoding**: console Windows (cp1252) lỗi khi `print` tiếng Việt có dấu → dùng ASCII trong `print` của script Python.
- Test nhỏ (`LIMIT`) để validate schema trước khi chạy full.

---

## Mô hình dữ liệu
- Bảng dạng **flow transition**: mỗi dòng là 1 bước chuyển màn `screen_from → screen_to`.
- **Sắp xếp luồng theo**: `event_timestamp`, tie-break `flow_row_number`, `event_row_in_flow`.
- **Version lấy từ cột `version`** (thuộc tính bản app, có trên MỌI event) — KHÔNG suy từ tên màn. Tên màn chỉ để biết user đi sâu tới đâu.
- Cột hay dùng: `user_pseudo_id`, `version`, `event_date`, `event_timestamp`, `screen_from`, `screen_to`, `session_number`, `country`, `traffic_source_medium`.

---

## Quy ước phân tích luồng intro
- Mỗi `user_pseudo_id` thuộc đúng 1 version & 1 luồng. **Không user nào lẫn intro6 ↔ intro7** (đã verify, both = 0).
- **Chữ ký màn theo version** (chỉ xuất hiện ở 1 version, dùng để gom mọi biến thể nhỏ về đúng luồng chính):
  | Version | Intro | Subscribe |
  |---------|-------|-----------|
  | 3.3.5 | `intro6*` | `subscribe5` |
  | 3.3.7 | `intro7*` | `subscribe5_new` |
- `onboarding_5_video*`, `intro2*` xuất hiện ở **cả 2 version** (nhỏ) → KHÔNG phải chữ ký riêng.
- **Nhận diện luồng tốt nhất = `intro OR subscribe`** (vét cả user nhảy thẳng subscribe / mất event intro).
- ⚠️ Cặp `home` ↔ `measure` bị "đảo" giữa 2 version (nghi khác định nghĩa/thứ tự màn) → chuẩn hóa trước khi so sánh phần sau Subscribe.

---

## Vẽ chart
- **Luôn vẽ bằng Plotly** (không matplotlib/seaborn).
- Áp palette Soft Report (theo global): nền `#ECF0F1`, text/primary `#2C3E50`, accent `#E74C3C`, cycle `["#2C3E50","#E74C3C","#2980B9","#27AE60","#F39C12"]`.
- **Chỉ xuất HTML** (`fig.write_html`), KHÔNG tạo file PNG cho user.
- **Tự verify layout**: render PNG tạm (`_tmp_verify.png`) qua `runpy.run_path(...)` rồi `fig.write_image`, đọc ảnh kiểm tra, **xoá ngay** sau khi xong. PNG export cần `kaleido` (đã cài).
- Ký tự `▼`/`⚠️` trong text của chart OK (Plotly UTF-8); chỉ console `print` mới lỗi cp1252.
- Conditional formatting: thang xanh→vàng→đỏ theo độ lớn (nhỏ=xanh, lớn=đỏ).

---

## Scripts vẽ chart (đã build)
- [build_funnel_chart.py](build_funnel_chart.py) — funnel splash→measure 2 version, 2 subplot cạnh nhau.
- [build_funnel_337.py](build_funnel_337.py) — funnel 1 version (3.3.7), tô màu 5 nhóm chức năng.
- [build_funnel_compare.py](build_funnel_compare.py) — **chart chính**: back-to-back 3.3.5 vs 3.3.7 (2 phễu quay vào nhau), giữ nguyên tên màn mỗi version, hàng align theo nhóm chức năng, kèm bảng chỉ số `vs %remain` + `vs %drop vs prev step (& ΔΔ)`. Output: [funnel_compare_335_337.html](funnel_compare_335_337.html).

---

## Phương pháp dựng funnel
- **Funnel = chuỗi `screen_from`** mỗi user, sắp theo `event_timestamp` (tie-break như trên).
- **Cắt tại lần đầu `screen_from = 'measure'`** (gồm cả measure); user không tới measure → giữ hết tới màn cuối session 1.
- **Metric mỗi màn = % distinct `user_pseudo_id`** chạm màn đó / tổng user version (baseline `splash` = 100%).
- **Drop**: `▼%` = drop tương đối so bước trước; `Δstep (pp)` = `%trước − %sau`.
- **Conditional formatting chỉ tính tới hết màn `subscribe`** (bỏ home/measure vì nghi đảo định nghĩa). Hàng chỉ 1 version có → bỏ qua, không tính delta.
- **5 nhóm chức năng** (để gom & so sánh):
  1. Khởi động & Đăng ký: `splash`, `sign_in_onboarding`
  2. Giới thiệu & Giáo dục: `intro*_heart_measure`, `learn_more`, `track_stress`, `heart_report`, `blood_pressure`, `blood_sugar`, `check_apple_watch`
  3. Phân tích & Khảo sát: `analyzing`, `select_gender/age/height/weight`, `question_health_issue`, `final_processing`
  4. Paywall: `subscribe5` / `subscribe5_new`
  5. Trải nghiệm chính: `home`, `measure`

---

## Tài liệu kết quả
Xem [note.md](note.md) — kết quả thống kê đã chạy + 4 query mẫu đã test (phân loại luồng kết hợp, deepest-stage, liệt kê chuỗi N màn).
