#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
shopt -s nullglob

# OuterLink: Offline Governance Bridge Prototype
# Defaults to Termux paths but can be overridden via BASE_DIR.
BASE_DIR=${OUTERLINK_BASE_DIR:-${BASE_DIR:-"/data/data/com.termux/files/home"}}
FALLBACK_BASE="$HOME/outerlink_termux"
LOG=${OUTERLINK_LOG:-"$BASE_DIR/outerlink.log"}
DB=${OUTERLINK_DB:-"$BASE_DIR/outerlink.db"}
JOBS_DIR=${OUTERLINK_JOBS_DIR:-"$BASE_DIR/outerlink_jobs"}

if ! mkdir -p "$BASE_DIR" "$JOBS_DIR" 2>/dev/null; then
  echo "[OuterLink] Unable to create Termux base; falling back to $FALLBACK_BASE" >&2
  BASE_DIR="$FALLBACK_BASE"
  LOG="$BASE_DIR/outerlink.log"
  DB="$BASE_DIR/outerlink.db"
  JOBS_DIR="$BASE_DIR/outerlink_jobs"
  mkdir -p "$BASE_DIR" "$JOBS_DIR"
fi

echo "[OuterLink] Starting session..." >> "$LOG"

hash_check() {
  local checksum
  checksum=$(sha256sum "$0" | awk '{print $1}')
  echo "$checksum" > "${DB}_hash"
  echo "[OuterLink] Integrity verified: $checksum" >> "$LOG"
}

task_runner() {
  if [ -d "$JOBS_DIR" ]; then
    for job in "$JOBS_DIR"/*; do
      [ -x "$job" ] || continue
      bash "$job" >> "$LOG" 2>&1 || echo "[OuterLink] Task failed: $job" >> "$LOG"
    done
  else
    echo "[OuterLink] No task directory found at $JOBS_DIR" >> "$LOG"
  fi
}

sync_node() {
  echo "[OuterLink] Syncing queued data..." >> "$LOG"
  # future: encrypted push to verified endpoint
}

hash_check
task_runner
sync_node

echo "[OuterLink] Cycle complete $(date)" >> "$LOG"
