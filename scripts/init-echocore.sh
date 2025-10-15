#!/usr/bin/env bash
set -e
git add README_AUTHORITY.md CONTRIBUTING.md .github/ attestions/ docs/ modules/ scripts/ || true
git commit -m "chore(echo): bootstrap EchoCore authority, CI, docs, attestations scaffold"
