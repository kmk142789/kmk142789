#!/usr/bin/env bash
set -euo pipefail

CACHE_DIR="outerlink_cache"
EVENT_LOG="outerlink_events.log"

if [ -d "$CACHE_DIR" ]; then
  for file in "$CACHE_DIR"/*.json; do
    [ -e "$file" ] || continue
    cat "$file" >> "$EVENT_LOG"
    echo >> "$EVENT_LOG"
    rm -f "$file"
  done
fi
