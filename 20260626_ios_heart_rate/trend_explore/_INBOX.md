# _INBOX.md — trend_explore / ios_heart_rate

## 2026-06-26
- [pattern] Overview Metrics query (đã verify khớp Looker Studio): JOIN 3 bảng theo install_date — (1) sdk_iap_installs: new_users, filter data_source='Adjust'; (2) sdk_iap_pay_start_cohort_all_product: purchase_start_users + iap_users, filter number_day_install=60 + data_source='Adjust'; (3) sdk_iap_conversion_cohort_all_product: sub_pay_actual_users, filter number_day_install=60 + data_source='Adjust'. pay_rate_start = SAFE_DIVIDE(purchase_start_users, new_users); pay_rate_actual = SAFE_DIVIDE(iap_users + sub_pay_actual_users, new_users). User Level → _users cols; Event Level → _total/_value cols.
- [caveat] Không filter data_source='Adjust' → installs và pay_start bị double count (Adjust + Firebase), new_users gấp đôi, pay_rate_actual giảm ~50%. Conversion table đã single-source nên không bị ảnh hưởng.
- [pattern] DOW median Pay Rate Start query (BQ): JOIN installs + pay_start theo install_date, filter data_source='Adjust' + number_day_install=60 + new_users>=100 (loại ngày nhiễu). Median dùng APPROX_QUANTILES(pay_rate_start,100)[OFFSET(50)]. EXTRACT(DAYOFWEEK): 1=Sun,2=Mon,...,7=Sat — ORDER BY cần map lại (Mon=1,...,Sun=7). Kết quả: Thứ 2 cao nhất (6.61%), Thứ 7 thấp nhất (5.74%), median toàn kỳ 6.01%.

## 2026-06-26 — Wrap

- [decision] Loại dimension country khỏi analysis (quá nhiều, coverage mỏng); phân tích theo tier (US tách riêng khỏi Tier01) và traffic_source_medium (CPP_* gộp vào FacebookW2A).
- [finding] Chu kỳ tuần được xác nhận toàn app: Thứ 2 cao nhất (6.61%), Thứ 7 thấp nhất (5.74%), biên độ ~14.5%. Appier là traffic source duy nhất có PACF lag-7 significant (real weekly driver). Tier01 excl US và Tier02 có pattern ~17–21 ngày, không phải weekly. US không có chu kỳ rõ.
- [caveat] Lag-6 significant trong ACF KHÔNG có nghĩa "chu kỳ 6 ngày" hay "thứ 2 cao → thứ 6 thấp". Ý nghĩa thực: đỉnh (thứ 2) và đáy (thứ 7) trong tuần cách nhau 5-6 ngày → tạo ra negative correlation tại lag 6. Chu kỳ thực vẫn là 7 ngày.
- [caveat] Các peak PRS cao (10–13%) trong tháng 5-6 khi installs thấp vẫn được tính vào analysis (new_users >= 100, không bị lọc). Peak này do traffic organic/high-intent còn lại khi UA spend giảm, KHÔNG phải product tốt hơn. Cân nhắc re-run với new_users >= 5,000 để kiểm tra DOW pattern trên installs bình thường.
- [caveat] Cohort day 60 = đo pay rate tại cột mốc 60 ngày sau install. User có thể cài thứ 2 nhưng trial thứ 6 — cohort day 60 capture được tất cả, số liệu chín hơn so với D0/D7.
- [pattern] PACF vs ACF: ACF lag-7 significant nhưng PACF lag-7 không significant → lag-7 là echo của lag-1+lag-6 (DOW pattern). Nếu PACF lag-7 significant → có real weekly driver độc lập (chỉ Appier traffic).
- [pattern] Khi PRS trên dashboard giảm thứ 7: kiểm tra tuần trước trước khi escalate. Rule: giảm <15% đúng thứ 7 → khả năng cao là tự nhiên, không phải sự cố.
- [open] Re-run analysis với filter new_users >= 5,000 để loại giai đoạn installs thấp (May-Jun) và verify DOW pattern không bị skew bởi các peak PRS cao.
