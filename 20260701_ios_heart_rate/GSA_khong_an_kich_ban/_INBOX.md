# _INBOX.md — GSA_khong_an_kich_ban

## 2026-07-01 — Wrap
- [decision] Dùng `traffic_source.name/medium/source` (cột resolved) để xác định user GSA, KHÔNG dùng `collected_traffic_source.*` — vì cột này 100% NULL trên iOS (đã kiểm chứng trên toàn bộ 67,219 events của campaign GSA trong 1 tháng, 0 event có gclid/manual_source).
- [caveat] `traffic_source` KHÔNG có sẵn ngay tại `first_open` cho toàn bộ user — chỉ 84% (204/243) resolve ngay lúc first_open. 16% (39/243) còn lại bị delay median 27h, mean 47h, max ~203h (8.4 ngày).
- [caveat] Event đã log trước khi attribution resolve giữ NULL vĩnh viễn (không backfill ngược) — Firebase chỉ gắn traffic_source cho các event log SAU thời điểm resolve, thường là event đầu của session/ngày mới (app_update, session_start, Get_Splash_Start...).
- [caveat] 39 user bị delay tập trung 100% vào 2 cụm ngày first_open: 2026-06-03→05 và 2026-06-17→19. Các ngày khác trong tháng (06-01, 06-06→12, 06-20→26, ~170 user) có 0 case delay → nghi ngờ sự cố cục bộ theo thời điểm (network/postback/pipeline) chứ không phải đặc tính chung của kênh GSA.
- [open] Chưa xác định nguyên nhân gốc của 2 cụm ngày delay — cần đối chiếu với team Ads/UA xem có đổi campaign, tracking link, hay network outage trong đúng các ngày đó.
- [open] Chưa xác nhận logic app hiện tại đọc field nào (traffic_source hay collected_traffic_source) và đọc tại thời điểm nào (first_open hay session sau) để quyết định hiển thị kịch bản GSA — đây là bước cần làm tiếp để chốt root cause.
- [pattern] Query mẫu: join `first_open` (MIN event_timestamp theo user) với event đầu tiên có `traffic_source.name = <campaign>` để đo delay resolve — tái dùng được cho các case điều tra attribution delay khác.
