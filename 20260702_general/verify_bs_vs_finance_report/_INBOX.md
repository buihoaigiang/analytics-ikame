# _INBOX.md — verify_bs_vs_finance_report

## 2026-07-02 — Wrap
- [decision] Nguồn ground truth để đối soát revenue là bảng finance Play Console (`zegobi-datacenters.stg_business.finance_playstore_ikame_app`), không phải Adjust — Adjust đếm order theo event SDK nên gấp ~6 lần order thật và không trừ Google fee (proceeds = gross), chỉ dùng để tham khảo xu hướng, không đối soát tài chính.
- [caveat] Khi so bảng API/BS (`dashboard-reservation-slot.allproject_business_3_1__revenue_iap.giangbh`) với finance, bắt buộc lọc `data_source = 'Playstore'` — `Firebase`/`Adjust` không cùng đơn vị đo.
- [caveat] `transaction_date` trong bảng finance là STRING dạng `"Apr 1, 2026"` — không dùng để filter khoảng ngày, phải dùng `event_date` (DATE).
- [caveat] Report finance trễ ~1 tháng — tháng mới nhất thường chỉ có vài ngày dữ liệu, phải loại ra khi tính tổng, chốt khung so sánh = đến hết tháng đầy đủ cuối cùng.
- [bug] Nguyên nhân lệch Net revenue giữa BS và Finance (~5.9% ở Clean_Android, Jan–May 2026): bảng API/BS đang **giả định cứng fee 20%** khi tính `*_proceeds`, trong khi Google fee thực tế của app này là **15%** (đo được 14.92–15.07% đồng đều trên 178 quốc gia — do subscription revenue chưa vượt ngưỡng $1M/năm nên còn ở mức ưu đãi 15%, chưa bị áp 30%). Gross khớp gần tuyệt đối (-0.05%) khi đã lọc đúng `data_source='Playstore'` — nên lỗi nằm ở công thức fee, không phải ở nguồn dữ liệu thô.
- [decision] Giả thuyết ban đầu (nghi do currency conversion, cấu trúc phí "15% service fee + 5% thuế = 20%") **bị bác bỏ** — thuế thực tế chỉ chiếm 0.02% gross toàn dataset, không phải 5%.
- [caveat] Thuế (Tax) trong bảng finance chỉ xuất hiện ở Egypt & Kuwait (Direct Carrier Billing Withholding Tax) — 176/178 quốc gia còn lại `Tax = 0` là **đúng, không phải thiếu data**, vì Google Play là merchant-of-record tự thu/nộp VAT cho các nước khác, không trừ vào payout developer.
- [caveat] Muốn biết net revenue thực nhận, dùng cột `Net` (= SUM toàn bộ `amount_merchant_in_usd`) của bảng finance — không dùng `total_revenue_subscription_proceeds` của bảng API vì cột đó ước tính sai fee rate.
- [pattern] Quy trình chuẩn để đối soát revenue Play Store vs API nội bộ cho bất kỳ app Android nào (schema, công thức, query mẫu) đã được document đầy đủ tại `C:\Users\admin\Desktop\20260702_verify_revenue\20270702_vrf_rev\REVENUE_COMPARISON.md` — tái dùng cho các app Android IAP/Sub khác đang bị nghi lệch.
- [open] Chưa kiểm tra các app Android khác ngoài Clean_Android — cần áp lại quy trình này cho từng app để xác nhận cùng nguyên nhân (fee rate giả định sai) hay có nguyên nhân khác.
- [open] Chưa sửa pipeline tính `*_proceeds` trong bảng BS để lấy fee rate động theo app (field `service_fee`) thay vì hardcode 20%.
