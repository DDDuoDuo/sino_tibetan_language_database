#!/usr/bin/env bash
set -Eeuo pipefail

REMOTE="${1:-renjun@47.113.104.70}"
REMOTE_DIR="${REMOTE_DIR:-/language/stsplit/backups/mysql/}"
LOCAL_DIR="${LOCAL_DIR:-$HOME/Documents/language_project/mysql_backups/}"

mkdir -p "$LOCAL_DIR"

if command -v rsync >/dev/null 2>&1; then
  rsync -avz --progress "$REMOTE:$REMOTE_DIR" "$LOCAL_DIR"
else
  scp -r "$REMOTE:$REMOTE_DIR"* "$LOCAL_DIR"
fi

echo "Backups copied to $LOCAL_DIR"
