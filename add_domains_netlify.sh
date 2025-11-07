#!/usr/bin/env bash
set -euo pipefail

NETLIFY_AUTH_TOKEN=${NETLIFY_AUTH_TOKEN:-""}
if [[ -z "$NETLIFY_AUTH_TOKEN" ]]; then
  echo "Error: NETLIFY_AUTH_TOKEN environment variable must be set." >&2
  exit 1
fi

if [[ ! -f domains.txt ]]; then
  echo "Error: domains.txt not found in $(pwd)." >&2
  exit 1
fi

while IFS= read -r DOMAIN || [[ -n "$DOMAIN" ]]; do
  [[ -z "$DOMAIN" ]] && continue
  echo "🔗 Linking $DOMAIN to Netlify..."
  RESPONSE=$(curl -s -X POST "https://api.netlify.com/api/v1/dns_zones" \
    -H "Authorization: Bearer $NETLIFY_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$DOMAIN\"}")
  if command -v jq >/dev/null 2>&1; then
    echo "$RESPONSE" | jq '.name, .id'
  else
    echo "$RESPONSE"
  fi
  echo
  sleep 1
done < domains.txt
