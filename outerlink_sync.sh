#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=${OUTERLINK_BASE_DIR:-}
CACHE_DEFAULT="outerlink_cache"
EVENT_DEFAULT="outerlink_events.log"
if [ -n "$BASE_DIR" ]; then
  CACHE_DEFAULT="$BASE_DIR/$CACHE_DEFAULT"
  EVENT_DEFAULT="$BASE_DIR/$EVENT_DEFAULT"
fi
CACHE_DIR=${OUTERLINK_CACHE_DIR:-$CACHE_DEFAULT}
EVENT_LOG=${OUTERLINK_EVENT_LOG:-$EVENT_DEFAULT}

mkdir -p "$CACHE_DIR"
mkdir -p "$(dirname "$EVENT_LOG")"

if [ -d "$CACHE_DIR" ]; then
  for file in "$CACHE_DIR"/*.json; do
    [ -e "$file" ] || continue
    cat "$file" >> "$EVENT_LOG"
    echo >> "$EVENT_LOG"
    rm -f "$file"
  done
fi
