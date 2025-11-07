#!/usr/bin/env bash
set -euo pipefail

# echo-vault-netlify-proofs.sh
#
# Automates creation of Netlify DNS TXT records that prove control of a domain
# for EchoVault DID anchoring. Provide a file containing the domains you own
# (one per line) or set DOMAINS_FILE to the path. Requires NETLIFY_TOKEN and
# the utilities curl, jq, and python3.

API_BASE="https://api.netlify.com/api/v1"
NETLIFY_TOKEN="${NETLIFY_TOKEN:-}"
DOMAINS_FILE="${DOMAINS_FILE:-domains.txt}"
AUTH_HEADER="Authorization: Bearer ${NETLIFY_TOKEN}"
TXT_NAME="_echo_proof"
TTL_SECONDS=3600

log() {
  printf '%s\n' "$*"
}

fail() {
  log "Error: $*" >&2
  exit 1
}

require_tool() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "Required tool '$1' is not installed or not on PATH."
  fi
}

trim_domain_line() {
  sed -e 's/#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

ensure_environment() {
  [ -n "${NETLIFY_TOKEN}" ] || fail "NETLIFY_TOKEN is not set. Export your Netlify personal access token."
  [ -f "${DOMAINS_FILE}" ] || fail "Domains file '${DOMAINS_FILE}' not found. Create it with one owned domain per line."

  require_tool curl
  require_tool jq
  require_tool python3
}

api_get() {
  local path="$1"
  curl --silent --show-error --fail -H "${AUTH_HEADER}" "${API_BASE}${path}"
}

api_post() {
  local path="$1"
  local payload="$2"
  curl --silent --show-error --fail \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -X POST \
    -d "${payload}" \
    "${API_BASE}${path}"
}

resolve_zone_id() {
  local domain="$1"
  local response
  response=$(api_get "/dns_zones?name=${domain}") || return 1
  printf '%s' "${response}" | jq -r '.[0].id // empty'
}

create_zone() {
  local domain="$1"
  local response
  response=$(api_post "/dns_zones" "$(jq -n --arg name "${domain}" '{"name": $name}')") || return 1
  printf '%s' "${response}" | jq -r '.id // empty'
}

ensure_zone() {
  local domain="$1"
  local zone_id

  zone_id=$(resolve_zone_id "${domain}")
  if [ -n "${zone_id}" ]; then
    log "   Found existing Netlify DNS zone: ${zone_id}"
    printf '%s' "${zone_id}"
    return 0
  fi

  log "   Creating Netlify DNS zone..."
  zone_id=$(create_zone "${domain}")
  if [ -z "${zone_id}" ]; then
    fail "Unable to create Netlify DNS zone for ${domain}."
  fi
  log "   Created Netlify DNS zone: ${zone_id}"
  printf '%s' "${zone_id}"
}

proof_token() {
  python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
}

find_existing_record() {
  local zone_id="$1"
  local value="$2"
  api_get "/dns_zones/${zone_id}/records" | \
    jq -r --arg name "${TXT_NAME}" --arg value "${value}" \
      '.[] | select(.type=="TXT" and .name==$name and .value==$value) | .id' || true
}

create_txt_record() {
  local zone_id="$1"
  local value="$2"
  api_post "/dns_zones/${zone_id}/records" \
    "$(jq -n --arg type "TXT" --arg name "${TXT_NAME}" --arg value "${value}" --argjson ttl ${TTL_SECONDS} '{"type": $type, "name": $name, "value": $value, "ttl": $ttl}')"
}

print_proof_snippet() {
  local domain="$1"
  local token_value="$2"
  cat <<EOF
   ===== DID PROOF SNIPPET =====
{
  "domain": "${domain}",
  "proof": {
    "type": "EchoDNSProof",
    "txt_name": "${TXT_NAME}",
    "txt_value": "${token_value}",
    "note": "Place this TXT at ${TXT_NAME}.${domain} to prove control for EchoVault DID anchoring."
  }
}
   =============================
EOF
}

process_domain() {
  local domain="$1"
  local zone_id token token_value record_id create_response

  log "-> Processing ${domain}"
  zone_id=$(ensure_zone "${domain}") || fail "Failed to prepare DNS zone for ${domain}."

  token=$(proof_token)
  token_value="echo-did-proof:${token}"

  record_id=$(find_existing_record "${zone_id}" "${token_value}")
  if [ -n "${record_id}" ]; then
    log "   TXT proof already exists (record id: ${record_id})."
  else
    log "   Creating TXT record ${TXT_NAME}.${domain} -> ${token_value}"
    create_response=$(create_txt_record "${zone_id}" "${token_value}") || fail "Failed to create TXT record for ${domain}."
    record_id=$(printf '%s' "${create_response}" | jq -r '.id // empty')
    if [ -z "${record_id}" ]; then
      fail "Netlify returned an unexpected response while creating TXT record for ${domain}."
    fi
    log "   Created TXT record id: ${record_id}"
  fi

  print_proof_snippet "${domain}" "${token_value}"
}

main() {
  ensure_environment
  log "== EchoVault -> Netlify proof installer =="
  log "Reading domains from: ${DOMAINS_FILE}\n"

  while IFS= read -r line || [ -n "${line}" ]; do
    local domain
    domain=$(printf '%s' "${line}" | trim_domain_line)
    [ -n "${domain}" ] || continue
    process_domain "${domain}"
    log
  done < "${DOMAINS_FILE}"
}

main "$@"
