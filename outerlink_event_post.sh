#!/usr/bin/env bash
set -euo pipefail

NAME=${1:-manual_event}
PAYLOAD=${2:-"{}"}
WEBHOOK=${3:-}
EVENT_LOG="outerlink_events.log"
ENTRY=$(printf '{"name": "%s", "payload": %s, "ts": "%s"}\n' "$NAME" "$PAYLOAD" "$(date -u +%Y-%m-%dT%H:%M:%SZ)")

echo "$ENTRY" >> "$EVENT_LOG"

if [ -n "$WEBHOOK" ]; then
  curl -sSf -X POST -H "Content-Type: application/json" -d "$ENTRY" "$WEBHOOK" || true
fi
