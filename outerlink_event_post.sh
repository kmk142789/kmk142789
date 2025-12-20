#!/usr/bin/env bash
set -euo pipefail

NAME=${1:-manual_event}
PAYLOAD=${2:-"{}"}
WEBHOOK=${3:-}
BASE_DIR=${OUTERLINK_BASE_DIR:-}
EVENT_LOG_DEFAULT="outerlink_events.log"
if [ -n "$BASE_DIR" ]; then
  EVENT_LOG_DEFAULT="$BASE_DIR/$EVENT_LOG_DEFAULT"
fi
EVENT_LOG=${OUTERLINK_EVENT_LOG:-$EVENT_LOG_DEFAULT}
ENTRY=$(printf '{"name": "%s", "payload": %s, "ts": "%s"}\n' "$NAME" "$PAYLOAD" "$(date -u +%Y-%m-%dT%H:%M:%SZ)")

mkdir -p "$(dirname "$EVENT_LOG")"
echo "$ENTRY" >> "$EVENT_LOG"

if [ -n "$WEBHOOK" ]; then
  curl -sSf -X POST -H "Content-Type: application/json" -d "$ENTRY" "$WEBHOOK" || true
fi
