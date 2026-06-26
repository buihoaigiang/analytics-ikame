## 2026-06-26

- [pattern] Để tổng hợp distinct parameter keys theo feature từ tracking plan Excel:
  1. Đọc file xlsx bằng `openpyxl`, sheet "Plan Tracking" (4 cols: Event Name, Type Layer, When trigger, Parameter Key)
  2. Column "Parameter Key" mỗi ô chứa nhiều keys ngăn cách bằng `\n` → split theo `\n`
  3. Dùng `defaultdict(list)` + `seen set` để collect keys theo thứ tự xuất hiện đầu tiên (không sort alphabet)
  4. Output ra `feature_parameter_keys.md` dạng bảng markdown, mỗi feature 1 section
  5. Output file: `tracking_ft/feature_parameter_keys.md`

- [decision] Cần aggregate distinct keys per feature để chuẩn bị update tracking cho phù hợp với hệ thống BI platform (PRMS integration)

- [open] Bước tiếp: map từng parameter key sang schema BI platform, xác định data type + naming convention phù hợp

## 2026-06-26 — Wrap

- [decision] Mục tiêu session: chuẩn bị tích hợp tracking ios_face_scanner lên PRMS qua BI platform — tracking đã gắn xong, cần aggregate keys để đối chiếu schema BI
- [pattern] Workflow aggregate distinct keys từ tracking plan Excel: đọc openpyxl → split `\n` trong cột Parameter Key → collect theo insertion order (defaultdict + seen set) → export markdown table
- [caveat] Thứ tự keys giữ nguyên theo lần xuất hiện đầu tiên trong file (không sort alpha) — quan trọng để dễ đối chiếu với flow màn hình
- [open] Chưa có data type, enum values, hoặc mapping sang BI schema — đây là việc cần làm tiếp
- [open] CLAUDE.md còn trống phần Country, Date range, Filter, Main table — cần điền khi xác định scope rõ hơn
