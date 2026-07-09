#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/language/stsplit}"
ENV_FILE="${ENV_FILE:-$APP_ROOT/backend/.env}"
BACKUP_DIR="${BACKUP_DIR:-$APP_ROOT/backups/mysql}"
MIN_FREE_KB="${MIN_FREE_KB:-2097152}" # 2 GB

mkdir -p "$BACKUP_DIR"
LOG_FILE="$BACKUP_DIR/backup.log"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"
}

fail() {
  log "ERROR: $*"
  echo "ERROR: $*" >&2
  exit 1
}

command -v mysqldump >/dev/null 2>&1 || fail "mysqldump is not installed"
command -v gzip >/dev/null 2>&1 || fail "gzip is not installed"

[ -r "$ENV_FILE" ] || fail "Cannot read env file: $ENV_FILE"

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

: "${DB_USER:?DB_USER is required in $ENV_FILE}"
: "${DB_PASS:?DB_PASS is required in $ENV_FILE}"
: "${DB_NAME:?DB_NAME is required in $ENV_FILE}"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"

if [ "$DB_HOST" = "host.docker.internal" ]; then
  DB_HOST="127.0.0.1"
fi

available_kb="$(df -Pk "$BACKUP_DIR" | awk 'NR==2 {print $4}')"
if [ -z "$available_kb" ] || [ "$available_kb" -lt "$MIN_FREE_KB" ]; then
  fail "Insufficient disk space for backup. Available KB: ${available_kb:-unknown}; required KB: $MIN_FREE_KB"
fi

timestamp="$(date '+%Y-%m-%d_%H-%M-%S')"
backup_file="$BACKUP_DIR/${DB_NAME}_${timestamp}.sql.gz"
tmp_file="$backup_file.tmp"

cleanup() {
  rm -f "$tmp_file"
}
trap cleanup EXIT

log "Starting MySQL backup for database '$DB_NAME' from $DB_HOST:$DB_PORT"

MYSQL_PWD="$DB_PASS" mysqldump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --user="$DB_USER" \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --default-character-set=utf8mb4 \
  "$DB_NAME" | gzip -c > "$tmp_file"

if [ ! -s "$tmp_file" ]; then
  fail "Backup file is empty: $tmp_file"
fi

mv "$tmp_file" "$backup_file"
chmod 600 "$backup_file"
log "Backup completed: $backup_file ($(du -h "$backup_file" | awk '{print $1}'))"

echo "$backup_file"
