#!/usr/bin/env bash
set -euo pipefail

# Requires: GitHub CLI authenticated with repo admin
REPO="${1:-$GITHUB_REPOSITORY}"

labels=(
  "track:glyph-cloud:#7aa2f7"
  "track:continuum:#8bd5ca"
  "track:memory-store:#eed49f"
  "track:federated-pulse:#c6a0f6"
  "track:opencode:#f5bde6"
  "track:wallets:#a6da95"
)

for l in "${labels[@]}"; do
  name="${l%%:*}"; rest="${l#*:}"; color="${rest##*:}"; text="${rest%:*}"
  gh label create "$name" --color "${color#\#}" --description "$text" --repo "$REPO" \
    || gh label edit "$name" --color "${color#\#}" --description "$text" --repo "$REPO"
done

# milestones
gh api -X POST "repos/$REPO/milestones" -f title="epoch/2023-quantinuum" || true
gh api -X POST "repos/$REPO/milestones" -f title="epoch/2025-quantinuum" || true

echo "✓ Labels and milestones ensured for $REPO"
