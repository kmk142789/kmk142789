# Chaos Testing Suite

This suite applies disruptive scenarios against a Kubernetes environment to
validate resiliency. Scenarios are orchestrated by `run_chaos.sh`, which
captures structured recovery metrics in `tests/chaos/results/chaos-summary.json`.

## Prerequisites

- `kubectl` installed locally or available in CI
- Access to a target cluster via `KUBECONFIG`
- Pods targeted for chaos should run inside a controller (e.g. Deployment) that
  automatically recreates workloads
- For network chaos the probe pod must include the `tc` binary (commonly
  available in distroless-plus or debian-based images)

## Configuring scenarios

Environment variables control which resources are exercised (the helper script
also depends on `python3` for JSON aggregation):

| Variable | Required for | Description |
|----------|--------------|-------------|
| `CHAOS_TARGET_NAMESPACE` | both | Namespace that hosts the workloads (default `default`). |
| `CHAOS_TARGET_SELECTOR` | pod deletion | Pod label selector identifying replicas to terminate. |
| `CHAOS_TARGET_DEPLOYMENT` | pod deletion | Deployment name used to wait for recovery. |
| `CHAOS_ROLLOUT_TIMEOUT` | pod deletion | Optional rollout timeout (default `300s`). |
| `CHAOS_NETWORK_PROBE_POD` | network latency | Pod name that accepts `kubectl exec`. |
| `CHAOS_NETWORK_INTERFACE` | network latency | Interface to shape (default `eth0`). |
| `CHAOS_NETWORK_LATENCY` | network latency | Delay injected via `tc netem` (default `100ms`). |
| `CHAOS_NETWORK_DURATION` | network latency | Seconds to keep latency active (default `30`). |

Example execution:

```bash
export CHAOS_TARGET_NAMESPACE="production"
export CHAOS_TARGET_SELECTOR="app=pulse-gateway"
export CHAOS_TARGET_DEPLOYMENT="pulse-gateway"
export CHAOS_NETWORK_PROBE_POD="pulse-gateway-0"
export KUBECONFIG="$HOME/.kube/config"
./tests/chaos/run_chaos.sh
```

The resulting JSON is ready for downstream observability ingestion or CI
artifacts.
