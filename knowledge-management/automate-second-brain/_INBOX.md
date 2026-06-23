# Inbox — automate-second-brain

## 2026-06-23 — Wrap
- [decision] README.md đặt trong `knowledge-management/automate-second-brain/` — folder này là meta-documentation về chính hệ thống, không phải code phân tích
- [pattern] Cấu trúc README 8-bước đủ để onboard từ đầu: git init → global CLAUDE.md → 3 hooks → settings.json → 2 slash commands → xong
- [decision] "new-project" là commit message convention (`new-project: <path>`), không phải slash command riêng — cần phân biệt rõ khi giải thích
- [caveat] `session_start.sh` hook chỉ chạy từ working directory mà Claude Code được mở — nếu mở từ subdirectory thì `_INBOX.md` sẽ không tự tạo ở root repo
- [pattern] Obsidian sync hoạt động bằng cách append toàn bộ `_INBOX.md` vào `Obsidian/_INBOX.md` — không dedup, cần xử lý thủ công nếu session_end chạy nhiều lần

## 2026-06-23 — Wrap (verify-cancel-android-vs-ios)
- [decision] D0 cancel rate Android thấp hơn iOS là tín hiệu thật và đáng tin — Android activation 27.8% vs iOS 36.4% (-8.6pp), trial 26.0% vs 51.0% (-25.0pp) ở US
- [decision] Product `discounted_offer` ($0.99 intro) trên Android mới là tín hiệu mạnh nhất: ever-cancel chỉ 20.7% (global) / 36.3% (US) — thấp hơn iOS activation 77.4% gần 2x
- [caveat] Ever-cancel rate cho `activation` product hội tụ về cùng điểm (74.6% cả 2 platform) — D0 thấp hơn KHÔNG đồng nghĩa retention tổng thể tốt hơn về dài hạn
- [caveat] Volume Android nhỏ hơn iOS 14x (5,832 vs 83,719 starts Jan–Jun 2026) — kết quả ổn định nhưng cần scale thêm data để confirm
- [caveat] Gap D0 trial (-25pp) có thể bị inflate bởi country mix: Android chạy nhiều PH hơn iOS, PH có D0 cancel thấp → cần country-controlled analysis để isolate behavioral signal
- [pattern] Adjust "cancellation rate" bị distort bởi event type khác nhau: iOS dùng `trial_started`, Android dùng `discounted_offer` — nếu Adjust count discounted_offer làm denominator thì Android rate trông thấp hơn rất nhiều (35.6% vs iOS 98%)
- [pattern] Apple fire cancel ngay khi user tắt auto-renewal (subscription vẫn còn hạn) → iOS `_subscription_cancelled_at_` = NULL; Google Play fire muộn hơn → Android có field này → timing event khác nhau về cơ chế
- [open] Country-controlled analysis (US-only by channel) để tách behavioral signal khỏi country mix effect
- [open] Kiểm tra Adjust dashboard đang dùng denominator nào cho cancellation rate — confirm `discounted_offer` có được tính không

## 2026-06-23 — Wrap (test-app/test-project-01)
- [decision] Tạo project scaffold `test-app/test-project-01` với CLAUDE.md cơ bản — chưa có analysis scope cụ thể
- [open] CLAUDE.md của test-project-01 còn trống phần Mô tả — cần điền khi đã rõ mục tiêu phân tích
- [pattern] Convention commit mới project: `new-project: <app>/<project-name>` — đồng nhất với init convention của repo
