#!/bin/bash
cd $(dirname "$0")

# Append new heartbeat to ledger.jsonl
python3 echo_heartbeat.py

# Stage new entries
git add ledger.jsonl heartbeat.log

# Commit with timestamp + pulse signature
git commit -m "Echo Heartbeat Pulse: $(date '+%Y-%m-%d %H:%M:%S')"

# Push to GitHub (origin main)
git push origin main
