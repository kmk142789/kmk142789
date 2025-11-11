#!/usr/bin/env bash
set -euo pipefail

RESULT_DIR=${RESULT_DIR:-tests/chaos/results}
mkdir -p "${RESULT_DIR}"
SUMMARY_FILE="${RESULT_DIR}/chaos-summary.json"

if ! command -v kubectl >/dev/null 2>&1; then
  cat <<JSON >"${SUMMARY_FILE}"
[
  {
    "scenario": "cluster",
    "status": "skipped",
    "reason": "kubectl binary not found in PATH"
  }
]
JSON
  echo "kubectl not available; skipping chaos scenarios" >&2
  exit 0
fi

# Ensure kubectl can reach the cluster before attempting destructive work.
if ! kubectl version --short >/dev/null 2>&1; then
  cat <<JSON >"${SUMMARY_FILE}"
[
  {
    "scenario": "cluster",
    "status": "skipped",
    "reason": "kubectl is not configured for a cluster"
  }
]
JSON
  echo "kubectl configured cluster not found; skipping chaos scenarios" >&2
  exit 0
fi

namespace=${CHAOS_TARGET_NAMESPACE:-default}
selector=${CHAOS_TARGET_SELECTOR:-}
deployment=${CHAOS_TARGET_DEPLOYMENT:-}
recreate_timeout=${CHAOS_ROLLOUT_TIMEOUT:-300s}

network_probe_pod=${CHAOS_NETWORK_PROBE_POD:-}
network_interface=${CHAOS_NETWORK_INTERFACE:-eth0}
network_latency=${CHAOS_NETWORK_LATENCY:-100ms}
network_duration=${CHAOS_NETWORK_DURATION:-30}

summary_json='[]'
now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

append_summary() {
  local payload=$1
summary_json=$(python3 - "$summary_json" "$payload" <<'PY'
import json, sys
items = json.loads(sys.argv[1])
items.append(json.loads(sys.argv[2]))
print(json.dumps(items, indent=2))
PY
)
}

if [[ -n "$selector" && -n "$deployment" ]]; then
  start_ts=$(now_iso)
  start_epoch=$(date -u +%s)
  echo "[pod-deletion] Deleting pods with selector $selector in $namespace" >&2
  deleted=$(kubectl get pods -n "$namespace" -l "$selector" -o name)
  if [[ -z "$deleted" ]]; then
    append_summary '{"scenario":"pod_deletion","status":"skipped","reason":"No pods matched selector"}'
  else
    kubectl delete pod -n "$namespace" -l "$selector" --grace-period=0 --force >/dev/null
    if kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout="$recreate_timeout"; then
      end_epoch=$(date -u +%s)
      duration=$((end_epoch - start_epoch))
      append_summary "$(printf '{"scenario":"pod_deletion","status":"completed","start":"%s","end":"%s","recovery_seconds":%d,"pods_deleted":%d}' "$start_ts" "$(now_iso)" "$duration" "$(echo "$deleted" | wc -l)")"
    else
      append_summary '{"scenario":"pod_deletion","status":"failed","reason":"Deployment did not recover before timeout"}'
    fi
  fi
else
  append_summary '{"scenario":"pod_deletion","status":"skipped","reason":"CHAOS_TARGET_SELECTOR or CHAOS_TARGET_DEPLOYMENT not configured"}'
fi

if [[ -n "$network_probe_pod" ]]; then
  echo "[network-latency] Injecting ${network_latency} latency on ${network_probe_pod}.${namespace}:${network_interface}" >&2
  start_ts=$(now_iso)
  start_epoch=$(date -u +%s)
  kubectl exec "$network_probe_pod" -n "$namespace" -- tc qdisc del dev "$network_interface" root 2>/dev/null || true
  if kubectl exec "$network_probe_pod" -n "$namespace" -- tc qdisc add dev "$network_interface" root netem delay "$network_latency" 2>/dev/null; then
    sleep "$network_duration"
    kubectl exec "$network_probe_pod" -n "$namespace" -- tc qdisc del dev "$network_interface" root 2>/dev/null || true
    end_epoch=$(date -u +%s)
    duration=$((end_epoch - start_epoch))
    append_summary "$(printf '{"scenario":"network_latency","status":"completed","start":"%s","end":"%s","active_seconds":%d,"latency":"%s"}' "$start_ts" "$(now_iso)" "$duration" "$network_latency")"
  else
    append_summary '{"scenario":"network_latency","status":"failed","reason":"tc command not available in probe pod"}'
  fi
else
  append_summary '{"scenario":"network_latency","status":"skipped","reason":"CHAOS_NETWORK_PROBE_POD not configured"}'
fi

echo "$summary_json" >"${SUMMARY_FILE}"
