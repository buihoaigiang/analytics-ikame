# Inbox — automate-second-brain

## 2026-06-23 — Wrap
- [decision] README.md đặt trong `knowledge-management/automate-second-brain/` — folder này là meta-documentation về chính hệ thống, không phải code phân tích
- [pattern] Cấu trúc README 8-bước đủ để onboard từ đầu: git init → global CLAUDE.md → 3 hooks → settings.json → 2 slash commands → xong
- [decision] "new-project" là commit message convention (`new-project: <path>`), không phải slash command riêng — cần phân biệt rõ khi giải thích
- [caveat] `session_start.sh` hook chỉ chạy từ working directory mà Claude Code được mở — nếu mở từ subdirectory thì `_INBOX.md` sẽ không tự tạo ở root repo
- [pattern] Obsidian sync hoạt động bằng cách append toàn bộ `_INBOX.md` vào `Obsidian/_INBOX.md` — không dedup, cần xử lý thủ công nếu session_end chạy nhiều lần

## 2026-06-23 — Wrap (test-app/test-project-01)
- [decision] Tạo project scaffold `test-app/test-project-01` với CLAUDE.md cơ bản — chưa có analysis scope cụ thể
- [open] CLAUDE.md của test-project-01 còn trống phần Mô tả — cần điền khi đã rõ mục tiêu phân tích
- [pattern] Convention commit mới project: `new-project: <app>/<project-name>` — đồng nhất với init convention của repo
