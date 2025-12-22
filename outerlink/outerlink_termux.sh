#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
shopt -s nullglob

# OuterLink: Offline Governance Bridge Prototype (Termux-optimized)
# Defaults to Termux paths but can be overridden via BASE_DIR.
BASE_DIR=${OUTERLINK_BASE_DIR:-${BASE_DIR:-"/data/data/com.termux/files/home"}}
FALLBACK_BASE="$HOME/outerlink_termux"
LOG=${OUTERLINK_LOG:-"$BASE_DIR/outerlink.log"}
DB=${OUTERLINK_DB:-"$BASE_DIR/outerlink.db"}
JOBS_DIR=${OUTERLINK_JOBS_DIR:-"$BASE_DIR/outerlink_jobs"}
CACHE_DIR=${OUTERLINK_CACHE_DIR:-"$BASE_DIR/outerlink_cache"}
QUEUE_DIR=${OUTERLINK_QUEUE_DIR:-"$BASE_DIR/outerlink_queue"}
QUEUE_FILE=${OUTERLINK_QUEUE_FILE:-"$QUEUE_DIR/build_queue.txt"}
SNAPSHOT=${OUTERLINK_SNAPSHOT:-"$BASE_DIR/outerlink_snapshot.json"}
BUILD_CMD=${OUTERLINK_BUILD_CMD:-""}
FALLBACK_BUILD_CMD=${OUTERLINK_BUILD_FALLBACK_CMD:-""}
DRAIN_QUEUE=${OUTERLINK_DRAIN_QUEUE:-"1"}
LIMITS_MODE=${OUTERLINK_LIMITS_MODE:-"1"}

if ! mkdir -p "$BASE_DIR" "$JOBS_DIR" "$CACHE_DIR" "$QUEUE_DIR" 2>/dev/null; then
  echo "[OuterLink] Unable to create Termux base; falling back to $FALLBACK_BASE" >&2
  BASE_DIR="$FALLBACK_BASE"
  LOG="$BASE_DIR/outerlink.log"
  DB="$BASE_DIR/outerlink.db"
  JOBS_DIR="$BASE_DIR/outerlink_jobs"
  CACHE_DIR="$BASE_DIR/outerlink_cache"
  QUEUE_DIR="$BASE_DIR/outerlink_queue"
  QUEUE_FILE="$QUEUE_DIR/build_queue.txt"
  SNAPSHOT="$BASE_DIR/outerlink_snapshot.json"
  mkdir -p "$BASE_DIR" "$JOBS_DIR" "$CACHE_DIR" "$QUEUE_DIR"
fi

echo "[OuterLink] Starting session..." >> "$LOG"

log_line() {
  echo "[OuterLink] $*" >> "$LOG"
}

hash_command() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
    return 0
  fi
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
    return 0
  fi
  if command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$1" | awk '{print $2}'
    return 0
  fi
  return 1
}

hash_check() {
  local checksum
  checksum=$(hash_command "$0" || true)
  if [ -z "$checksum" ]; then
    log_line "Integrity hash unavailable (sha256sum/shasum/openssl missing)."
    return 0
  fi
  echo "$checksum" > "${DB}_hash"
  log_line "Integrity verified: $checksum"
}

write_snapshot() {
  local termux_detected="false"
  if [ -d "/data/data/com.termux" ]; then
    termux_detected="true"
  fi
  cat > "$SNAPSHOT" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "termux": $termux_detected,
  "base_dir": "$BASE_DIR",
  "jobs_dir": "$JOBS_DIR",
  "cache_dir": "$CACHE_DIR",
  "queue_file": "$QUEUE_FILE",
  "build_cmd": "${BUILD_CMD:-null}",
  "fallback_build_cmd": "${FALLBACK_BUILD_CMD:-null}",
  "limits_mode": "$LIMITS_MODE",
  "commands": {
    "bash": "$(command -v bash 2>/dev/null || true)",
    "python3": "$(command -v python3 2>/dev/null || true)",
    "node": "$(command -v node 2>/dev/null || true)",
    "git": "$(command -v git 2>/dev/null || true)"
  }
}
EOF
  log_line "Snapshot written: $SNAPSHOT"
}

task_runner() {
  if [ -d "$JOBS_DIR" ]; then
    for job in "$JOBS_DIR"/*; do
      [ -x "$job" ] || continue
      bash "$job" >> "$LOG" 2>&1 || log_line "Task failed: $job"
    done
  else
    log_line "No task directory found at $JOBS_DIR"
  fi
}

sync_node() {
  log_line "Syncing queued data..."
  # future: encrypted push to verified endpoint
}

queue_build() {
  local cmd="$1"
  mkdir -p "$QUEUE_DIR"
  printf "%s|%s\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$cmd" >> "$QUEUE_FILE"
  log_line "Build queued: $cmd"
}

drain_build_queue() {
  [ "$DRAIN_QUEUE" = "1" ] || return 0
  [ -f "$QUEUE_FILE" ] || return 0
  local temp_queue
  temp_queue="${QUEUE_FILE}.tmp"
  : > "$temp_queue"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    local cmd="${line#*|}"
    if bash -lc "$cmd" >> "$LOG" 2>&1; then
      log_line "Queued build succeeded: $cmd"
    else
      printf "%s\n" "$line" >> "$temp_queue"
      log_line "Queued build failed, keeping: $cmd"
    fi
  done < "$QUEUE_FILE"
  mv "$temp_queue" "$QUEUE_FILE"
}

run_build() {
  [ -n "$BUILD_CMD" ] || return 0
  if [ "$LIMITS_MODE" = "1" ]; then
    export MAKEFLAGS="${MAKEFLAGS:--j1}"
    export NPM_CONFIG_FUND="${NPM_CONFIG_FUND:-false}"
    export NPM_CONFIG_AUDIT="${NPM_CONFIG_AUDIT:-false}"
    export PIP_DISABLE_PIP_VERSION_CHECK="${PIP_DISABLE_PIP_VERSION_CHECK:-1}"
    export CARGO_TERM_COLOR="${CARGO_TERM_COLOR:-always}"
    export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
  fi

  local tool="${BUILD_CMD%% *}"
  if ! command -v "$tool" >/dev/null 2>&1; then
    log_line "Build tool missing ($tool). Queueing build for later."
    queue_build "$BUILD_CMD"
    return 0
  fi

  if bash -lc "$BUILD_CMD" >> "$LOG" 2>&1; then
    log_line "Build completed: $BUILD_CMD"
    return 0
  fi

  log_line "Build failed: $BUILD_CMD"
  if [ -n "$FALLBACK_BUILD_CMD" ]; then
    local fallback_tool="${FALLBACK_BUILD_CMD%% *}"
    if command -v "$fallback_tool" >/dev/null 2>&1; then
      if bash -lc "$FALLBACK_BUILD_CMD" >> "$LOG" 2>&1; then
        log_line "Fallback build completed: $FALLBACK_BUILD_CMD"
        return 0
      fi
      log_line "Fallback build failed: $FALLBACK_BUILD_CMD"
    else
      log_line "Fallback tool missing ($fallback_tool)."
    fi
  fi

  queue_build "$BUILD_CMD"
}

hash_check
write_snapshot
drain_build_queue
run_build
task_runner
sync_node

log_line "Cycle complete $(date)"
