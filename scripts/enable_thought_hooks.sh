#!/usr/bin/env bash
set -e
mkdir -p .githooks
chmod +x .githooks/commit-msg
git config core.hooksPath .githooks
echo "✓ commit-msg hook enabled (dual-trace trailers)"
