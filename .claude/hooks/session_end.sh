#!/bin/bash
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
git add -A
git diff --cached --quiet || git commit -m "session-end: $(basename $PWD) $DATE $TIME"
INBOX="C:/Users/admin/Desktop/Obsidian/_INBOX.md"
[ -f "_INBOX.md" ] && [ -f "$INBOX" ] && cat "_INBOX.md" >> "$INBOX"
echo "[SessionEnd] Done"
