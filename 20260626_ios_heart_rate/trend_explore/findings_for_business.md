# Pay Rate Start — Có chu kỳ tuần không?
**Dành cho: UA Team, Product Team**
_ios_heart_rate · Jan–Jun 2026 · Cohort day 60_

---

## Câu chuyện bắt đầu từ đâu

Tuần vừa rồi, team chạy A/B test 50/50 vào **thứ 6**. Sáng **chủ nhật**, mọi chỉ số pay rate đều gãy. Team tắt test → chỉ số hồi lại. Câu hỏi đặt ra: **đây có thực sự là do A/B test gây ra không, hay chỉ số đang dao động theo chu kỳ tự nhiên?**

---

## Phát hiện chính

> **Pay Rate Start dao động theo ngày trong tuần với biên độ ~14.5%.**

| Ngày | Pay Rate Start |
|------|---------------|
| **Thứ 2** (cao nhất) | **6.61%** |
| Thứ 3 | 5.93% |
| Thứ 4 | 6.16% |
| Thứ 5 | 6.04% |
| Thứ 6 | 6.21% |
| **Thứ 7** (thấp nhất) | **5.74%** |
| Chủ nhật | 6.23% |

_Median toàn kỳ: 6.01%_

**Đây không phải ngẫu nhiên.** Phân tích thống kê (kiểm định tự tương quan) xác nhận: chu kỳ 6–7 ngày tồn tại ở cấp độ toàn app. Thứ 7 thấp hơn thứ 2 tới **~15%** — hoàn toàn có thể bị nhầm là "sự cố" nếu không biết trước.

---

## Giải thích đơn giản — "Kiểm định chu kỳ" là gì?

Hãy hình dung pay rate như **nhiệt độ trong ngày**: luôn có buổi sáng lạnh và buổi chiều ấm, không phụ thuộc vào việc bạn có làm gì hay không. Chúng tôi dùng 2 bài kiểm tra thống kê để xác nhận:

- **Bài test 1 (ACF):** "Có sự tương quan có ý nghĩa thống kê giữa ngày hôm nay và các ngày trước đó không?" → **Có** ở lag 1 và lag 6, với độ tin cậy 95%.
- **Bài test 2 (PACF):** "Lag 6 này là driver độc lập hay chỉ là hiệu ứng dây chuyền từ ngày hôm qua?" → Lag 6 là **driver độc lập** (thứ 7 tự nhiên thấp, không phải vì thứ 6 cao kéo xuống).

Kết quả: **chu kỳ 7 ngày (hàng tuần) là thật và có nguyên nhân riêng**, không chỉ là "echo" của ngày trước.

### Lag 6 có nghĩa là gì — và tại sao KHÔNG phải "chu kỳ 6 ngày"?

Câu hỏi hay thường gặp: *"Lag-6 có nghĩa là thứ 2 cao → thứ 6 thấp?"*

**Không đúng.** Chu kỳ vẫn là **7 ngày (1 tuần)**. Lag-6 chỉ là cách thống kê "phát hiện" ra rằng đỉnh (thứ 2) và đáy (thứ 7) trong tuần cách nhau 5–6 ngày. Các cặp ngày tạo ra signal mạnh nhất:

| Ngày thấp | → 6 ngày sau | Ngày cao |
|-----------|-------------|---------|
| Thứ 3 (5.93%) | → Thứ 2 tuần sau (6.61%) | +0.67pp |
| Thứ 7 (5.74%) | → Thứ 6 tuần sau (6.21%) | +0.48pp |
| Chủ nhật (6.23%) | → Thứ 7 (5.74%) | -0.49pp |

**Rule đơn giản cho business:** Không cần nghĩ về lag — nhìn thẳng bảng DOW phía trên. **Thứ 2 luôn cao (~6.6%), thứ 7 luôn thấp (~5.7%), lặp lại mỗi tuần.** Lag-6 chỉ là thuật ngữ kỹ thuật xác nhận pattern đó có ý nghĩa thống kê.

---

## Quay lại câu chuyện A/B test

Timeline thực tế:

```
Thứ 6 (launch test)  → PRS = 6.21%  [bình thường, hơi cao]
Thứ 7                → PRS = 5.74%  [THẤP NHẤT TUẦN — tự nhiên]
Chủ nhật sáng        → team thấy "gãy" → tắt test
Thứ 2                → PRS = 6.61%  [CAO NHẤT TUẦN — tự nhiên]  ← "hồi lại"
```

**Khả năng cao:** chỉ số không bị gãy bởi A/B test. Thứ 7 vốn đã thấp nhất tuần. Việc tắt test vào cuối thứ 7/đầu chủ nhật và thấy "hồi" sang thứ 2 là trùng khớp với chu kỳ tự nhiên.

> ⚠️ Điều này **không có nghĩa là A/B test vô tội** — cần kiểm tra riêng. Nhưng chu kỳ này là lý do đủ để không kết luận vội.

---

## Action items cho các team

### 1. A/B Test — chạy ít nhất 7 ngày (1 chu kỳ đầy đủ)
- Không kết luận từ 2–3 ngày đầu
- Nên **bắt đầu vào thứ 2** (đầu chu kỳ) để đo được cả đỉnh lẫn đáy trong cùng 1 chu kỳ
- Nếu không đủ 7 ngày, ít nhất cần **cùng số ngày thứ X** ở cả 2 variants

### 2. Deploy / Update app — tránh sai thời điểm
- **Không deploy vào thứ 6 hoặc cuối tuần**: thứ 7 tự nhiên giảm, dễ đổ lỗi cho phiên bản mới
- Nên deploy vào **thứ 2 hoặc thứ 3**: nếu có vấn đề, dễ phân biệt vì chỉ số đang ổn định
- Nếu bắt buộc deploy thứ 6: cần theo dõi so với **thứ 6 tuần trước** thay vì so với thứ 5 cùng tuần

### 3. UA Spend — phân bổ theo ngày trong tuần
- **Không tăng spend đột biến vào thứ 6/7**: install tăng nhưng pay rate thấp → cost/trial cao hơn bình thường
- **Thứ 2 có PRS cao nhất** → nếu muốn tối ưu trial rate, ưu tiên installs thứ 2
- Khi so sánh campaign theo ngày: luôn dùng **cùng distribution ngày trong tuần** để so fair

### 4. Đọc dashboard — tránh báo động giả
- Khi thấy chỉ số giảm thứ 7, **kiểm tra tuần trước có pattern tương tự không** trước khi escalate
- Rule of thumb: nếu giảm <15% và đúng thứ 7 → khả năng cao là tự nhiên

---

## Lưu ý quan trọng

| Segment | Có chu kỳ tuần rõ không? |
|---------|--------------------------|
| Toàn app (aggregate) | ✅ Có, lag 6–7 confirmed |
| Appier traffic | ✅ Có (mạnh nhất trong các nguồn) |
| Tier01 (excl. US) | ⚠️ Có pattern ~17 ngày (không phải weekly) |
| Tier02 | ⚠️ Có pattern ~18–21 ngày |
| United States | ❌ Không có chu kỳ rõ |
| FacebookW2A | ❌ Yếu, biên độ chỉ 4.6% |

→ Các rule trên áp dụng **toàn app**. Với US riêng lẻ thì không cần lo về thứ 7.

---

_Phân tích: DS Team · 2026-06-26 · Dữ liệu: Adjust, cohort day 60, User Level_
