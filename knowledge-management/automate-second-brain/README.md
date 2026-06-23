# Second Brain Tự Động — Obsidian + GitHub + Claude Code

> Hệ thống capture insight tự động khi làm việc với Claude Code.  
> Mọi session đều tự commit lên GitHub và sync sang Obsidian — không cần nhớ làm bằng tay.

---

## Tổng quan kiến trúc

```
Claude Code session
      │
      ├─ SessionStart  → tạo _INBOX.md nếu chưa có
      ├─ /note         → ghi insight ngay khi phát hiện
      ├─ PreCompact    → đánh dấu khi context bị nén
      ├─ /wrap         → tổng hợp session + commit
      └─ SessionEnd    → auto git commit + sync Obsidian
```

**Hai nơi lưu trữ, hai mục đích:**

| Nơi | Lưu gì | Path |
|-----|--------|------|
| **GitHub** | Code, query, workflow, CLAUDE.md | `C:\Users\admin\Desktop\analytics-ikame\` |
| **Obsidian** | Insight, decision, caveat, method | `C:\Users\admin\Desktop\Obsidian\` |

- **GitHub** = "Làm *như thế nào*" → code đã test, WORKFLOW.md
- **Obsidian** = "Tại sao làm vậy" → decision, limitation, pattern tái dụng

---

## 8 Bước Setup

### Bước 1 — Tạo repo git cho analytics

```powershell
cd C:\Users\admin\Desktop
mkdir analytics-ikame
cd analytics-ikame
git init
git remote add origin <github-url>
```

Import project đầu tiên vào đúng cấu trúc thư mục:

```
analytics-ikame/
├── ios-heart-rate/
│   └── funnel/
│       └── intro7-vs-intro6/   ← project đầu tiên
└── _knowledge/                 ← mirror Obsidian (tạo ở bước sau)
```

---

### Bước 2 — Tạo `~/.claude/CLAUDE.md` global

File này áp dụng cho **mọi project** khi dùng Claude Code.

```markdown
# CLAUDE.md — Global

## Ngôn ngữ
Luôn trả lời bằng tiếng Việt.

## Cấu trúc Second Brain
| Nơi | Lưu gì | Path |
|-----|--------|------|
| GitHub | Code, query, CLAUDE.md | C:\Users\admin\Desktop\analytics-ikame\ |
| Obsidian | Insight, decision, pattern | C:\Users\admin\Desktop\Obsidian\ |

## Second Brain — Auto Capture
### Hooks (trong .claude/settings.json project)
- SessionStart → tạo _INBOX.md nếu chưa có
- SessionEnd   → git commit + sync sang Obsidian
- PreCompact   → đánh dấu compact event

### Slash commands
- /note <insight> → ghi nhanh vào _INBOX.md
- /wrap           → tổng hợp session + update docs + git commit
```

> File nằm tại `C:\Users\admin\.claude\CLAUDE.md`.  
> Khi mâu thuẫn với CLAUDE.md trong project, ưu tiên file project.

---

### Bước 3 — Tạo thư mục hooks

```powershell
cd C:\Users\admin\Desktop\analytics-ikame
mkdir .claude\hooks
```

---

### Bước 4 — Viết `session_start.sh`

**File:** `.claude/hooks/session_start.sh`

```bash
#!/bin/bash
mkdir -p data/outputs
[ ! -f "_INBOX.md" ] && echo "# Inbox — $(basename $PWD)" > "_INBOX.md"
echo "[SessionStart] Ready"
```

**Tác dụng:**
- Tạo thư mục `data/outputs` nếu chưa có
- Tạo `_INBOX.md` nếu chưa có (không ghi đè nếu đã tồn tại)

---

### Bước 5 — Viết `session_end.sh`

**File:** `.claude/hooks/session_end.sh`

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
git add -A
git diff --cached --quiet || git commit -m "session-end: $(basename $PWD) $DATE $TIME"
# Sync INBOX sang Obsidian
INBOX="C:/Users/admin/Desktop/Obsidian/_INBOX.md"
[ -f "_INBOX.md" ] && [ -f "$INBOX" ] && cat "_INBOX.md" >> "$INBOX"
echo "[SessionEnd] Done"
```

**Tác dụng:**
- Auto commit toàn bộ thay đổi khi kết thúc session
- Append nội dung `_INBOX.md` vào `C:\Users\admin\Desktop\Obsidian\_INBOX.md`
- Chỉ commit nếu có thay đổi thực sự (`--quiet` guard)

---

### Bước 6 — Viết `pre_compact.sh`

**File:** `.claude/hooks/pre_compact.sh`

```bash
#!/bin/bash
echo "## COMPACT $(date +%Y-%m-%d\ %H:%M)" >> "_INBOX.md"
echo "- [system] Context compact tại đây" >> "_INBOX.md"
```

**Tác dụng:** Đánh dấu vào INBOX khi Claude Code nén context — để sau này biết có khoảng trống trong lịch sử.

---

### Bước 7 — Kết nối hooks vào `settings.json`

**File:** `.claude/settings.json`

```json
{
  "hooks": {
    "SessionStart": [
      {"matcher": "*", "hooks": [{"type": "command", "command": "bash .claude/hooks/session_start.sh"}]}
    ],
    "SessionEnd": [
      {"matcher": "*", "hooks": [{"type": "command", "command": "bash .claude/hooks/session_end.sh"}]}
    ],
    "PreCompact": [
      {"matcher": "*", "hooks": [{"type": "command", "command": "bash .claude/hooks/pre_compact.sh"}]}
    ]
  }
}
```

> Hooks chạy bash, nên cần Git Bash được cài và có trong PATH.

---

### Bước 8 — Tạo slash commands `/note` và `/wrap`

**File:** `.claude/commands/note.md`

```markdown
# /note — Ghi nhanh insight vào _INBOX.md
Append vào _INBOX.md:
- Nếu chưa có section hôm nay thì tạo `## YYYY-MM-DD`
- Thêm dòng `- [tag] $ARGUMENTS`
- Tag tự chọn: decision / caveat / pattern / open / bug
- Xác nhận 1 dòng ngắn, không làm gì thêm
```

**File:** `.claude/commands/wrap.md`

```markdown
# /wrap — Kết thúc session
1. Nhìn lại conversation → rút ra decision, caveat, pattern, open
2. Append vào _INBOX.md với section ## YYYY-MM-DD — Wrap
3. Cập nhật CLAUDE.md nếu có quy ước mới
4. git add -A && git commit
5. Báo tóm tắt những gì đã làm
```

---

## Lệnh `new-project`

Khi bắt đầu một project phân tích mới, dùng convention sau để tạo cấu trúc chuẩn:

```powershell
# Tạo folder structure
$PROJECT = "ios-heart-rate/experiments/new-analysis"
mkdir "C:\Users\admin\Desktop\analytics-ikame\$PROJECT"
cd "C:\Users\admin\Desktop\analytics-ikame\$PROJECT"

# Init project
echo "# CLAUDE.md — $PROJECT" > CLAUDE.md
git add -A
git commit -m "new-project: $PROJECT"
```

**Convention commit message:** `new-project: <đường-dẫn-từ-root>`

Cấu trúc thư mục chuẩn của một project:

```
<project-name>/
├── CLAUDE.md        ← context + quy ước riêng cho project này
├── WORKFLOW.md      ← các bước thực hiện
├── _INBOX.md        ← tự tạo bởi SessionStart hook
├── data/
│   └── outputs/     ← tự tạo bởi SessionStart hook
└── gcloud_credentials.json  ← KHÔNG commit (thêm vào .gitignore)
```

---

## Cách dùng hàng ngày

### Ghi insight ngay khi phát hiện

```
/note [decision] Dùng LIMIT trước khi chạy full query vì BigQuery tính tiền theo bytes scan
/note [caveat] authorized_user credential phải truyền project='team-begamob' tường minh
/note [pattern] Funnel chart nên normalize theo cohort size, không dùng absolute number
/note [bug] Encoding lỗi khi in tiếng Việt → fix bằng PYTHONIOENCODING=utf-8
/note [open] Cần kiểm tra xem intro7 có better D7 retention hơn intro6 không?
```

### Kết thúc session

```
/wrap
```

Claude sẽ:
1. Đọc lại toàn bộ conversation
2. Rút ra insights → append vào `_INBOX.md`
3. Cập nhật CLAUDE.md nếu có quy ước mới
4. Commit toàn bộ lên GitHub

### Xem lại insight

Mở `C:\Users\admin\Desktop\Obsidian\_INBOX.md` trong Obsidian — tất cả insights từ mọi session đều được append vào đây.

---

## Format `_INBOX.md`

```markdown
# Inbox — analytics-ikame

## 2026-06-23
- [decision] lý do quyết định X thay vì Y
- [caveat]   limitation cần nhớ
- [pattern]  tip tái dụng được cho project khác
- [open]     câu hỏi chưa giải quyết
- [bug]      lỗi gặp phải + cách fix

## COMPACT 2026-06-23 14:30
- [system] Context compact tại đây

## 2026-06-23 — Wrap
- [decision] ...
- [pattern]  ...
```

---

## Troubleshooting

| Vấn đề | Nguyên nhân | Fix |
|--------|-------------|-----|
| Hook không chạy | Git Bash chưa trong PATH | Thêm `C:\Program Files\Git\bin` vào PATH |
| INBOX không sync Obsidian | `_INBOX.md` Obsidian chưa có | Tạo file trống tại `C:\Users\admin\Desktop\Obsidian\_INBOX.md` |
| Commit không có gì | Không có thay đổi | Bình thường — `--quiet` guard ngăn empty commit |
| Hook chạy sai thư mục | Hook chạy từ project root | Đảm bảo `_INBOX.md` nằm ở root của project |

---

## Cấu trúc file sau khi setup

```
analytics-ikame/
├── .claude/
│   ├── settings.json           ← kết nối hooks
│   ├── hooks/
│   │   ├── session_start.sh
│   │   ├── session_end.sh
│   │   └── pre_compact.sh
│   └── commands/
│       ├── note.md             ← /note command
│       └── wrap.md             ← /wrap command
├── .gitignore                  ← bỏ gcloud_credentials.json
├── CLAUDE.md                   ← quy ước global (nếu có)
└── ios-heart-rate/
    └── funnel/
        └── intro7-vs-intro6/
            ├── CLAUDE.md
            ├── WORKFLOW.md
            └── _INBOX.md
```

---

*Setup ngày 2026-06-23 | analytics-ikame*
