# CLAUDE.md -- verify_bs_vs_finance_report

## Description
Verify chênh lệch revenue giữa Adjust và BS (Billing System). Phát hiện ban đầu: sau khi trừ thuế 20%, Adjust khớp với Play Console, nhưng vẫn lệch với BS. Nghi ngờ ban đầu là do quy đổi tiền tệ (currency conversion).

**Kết luận đã xác nhận (Clean_Android, Jan–May 2026):** nghi vấn currency conversion **bị bác bỏ**. Nguyên nhân thật là bảng API/BS giả định cứng Google fee = 20% khi tính `*_proceeds`, trong khi fee thực tế của app là **15%** (đo đồng đều 14.92–15.07% trên 178 quốc gia). Thuế chỉ chiếm 0.02% gross (chỉ Egypt/Kuwait qua Direct Carrier Billing), không phải 5% như giả định. Gross khớp gần tuyệt đối giữa finance và API khi lọc đúng `data_source='Playstore'` — lỗi nằm ở công thức fee, không phải nguồn dữ liệu thô. Chi tiết đầy đủ: `C:\Users\admin\Desktop\20260702_verify_revenue\20270702_vrf_rev\REVENUE_COMPARISON.md`.

## Quy ước đối soát revenue (đã kiểm chứng)
- Ground truth = `zegobi-datacenters.stg_business.finance_playstore_ikame_app` (finance export Play Console), dùng cột `event_date` để filter (KHÔNG dùng `transaction_date` — là STRING).
- So với bảng API nội bộ `dashboard-reservation-slot.allproject_business_3_1__revenue_iap.giangbh` phải lọc `data_source = 'Playstore'` — Adjust/Firebase không cùng đơn vị đo (Adjust đếm order gấp ~6 lần, không trừ Google fee).
- Report finance trễ ~1 tháng → loại tháng cuối chưa đủ ngày trước khi tổng hợp.
- Net revenue thực nhận = cột `Net` (SUM toàn bộ `amount_merchant_in_usd`) của bảng finance, KHÔNG dùng `*_proceeds` của bảng API (giả định fee sai).

## Bối cảnh / Yêu cầu (từ chat)
- Cấu trúc phí tổng: service fee 15% + thuế các quốc gia (thập cẩm, nhiều mức khác nhau theo quốc gia) 5% = **total 20%**
- Vấn đề: Adjust và BS đang lệch revenue với nhau
- Phạm vi lỗi: tất cả app **Android** có **IAP/Subscription** đều bị lệch
- Ưu tiên check trước: app **Clean**
- Chi tiết lệch: sau khi trừ 20% thuế, Adjust về **same** với Play Console → nhưng Adjust vẫn lệch với BS
- Nghi vấn (từ trao đổi với Nam): có thể do **quy đổi tiền tệ (currency conversion)** giữa các nguồn
- Mục tiên: chuẩn hoá lại số liệu (chuẩn số), để cả team follow theo
- Deadline mong muốn: triển khai xong trong ngày mai

## Scope
- App: Android, có IAP/Subscription — check trước app **Clean**
- Country: nhiều quốc gia (thuế khác nhau theo quốc gia)
- Date range:
- Filter: so sánh Adjust vs BS vs Play Console, sau khi trừ tổng phí 20% (15% service fee + 5% thuế)

## Data Source
- BQ Project: team-begamob
- Main table:
- Credential: gcloud_credentials.json (DO NOT commit)

## Session Management
- /note <insight>
- /wrap