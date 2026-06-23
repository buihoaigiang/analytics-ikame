#!/bin/bash
mkdir -p data/outputs
[ ! -f "_INBOX.md" ] && echo "# Inbox — $(basename $PWD)" > "_INBOX.md"
echo "[SessionStart] Ready"
