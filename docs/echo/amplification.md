# Amplification Engine

EchoEvolver now ships with the Amplification Engine, a deterministic layer that
measures, amplifies, and forecasts creative momentum for every cycle.  The
engine emits per-cycle snapshots, stores them in `state/amplify_log.jsonl`, and
surfaces rich feedback through the CLI and CI gates.

## Core Metrics

Each cycle is evaluated across six metrics:

| Metric | Description | How it is measured |
| ------ | ----------- | ------------------ |
| **Resonance** | Emotional alignment of the crew | Blend of joy, curiosity, and moderated rage from the emotional drive |
| **Freshness Half Life** | Signal decay since the cycle began | Exponential half-life based on the captured cycle duration |
| **Novelty Delta** | Degree of mythocode change | Jaccard distance between the current and previous rule sets |
| **Cohesion** | Completion of the recommended ritual | Ratio of completed steps to the expected orchestration order |
| **Coverage** | Engagement breadth of entities | Fraction of active entities in the state ledger |
| **Stability** | Operational steadiness | Average of CPU, node, and orbital metrics (with volatility as `1 - stability`) |

All metrics are normalised to `[0, 1]` and persisted with four decimal places so
snapshots remain byte-for-byte stable.

## Amplify Index

The Amplify Index combines the metrics into a 0–100 score using a tunable weight
profile:

```
index = wr * resonance
        + wf * freshness_half_life
        + wn * novelty_delta
        + wc * cohesion
        + wcov * coverage
        - ws * volatility
```

The default weights are chosen to reward creativity and consistency: resonance
(24), freshness (15), novelty (20), cohesion (14), coverage (15), volatility
(10).  Update the profile via `AmplificationEngine(weight_profile=...)` if you
need to emphasise different qualities.

## Nudges & Feedback

Whenever a metric drops below its threshold the engine emits auto-nudges such as
“Low novelty: mutate rule space with glyph perturbation X.”  Nudges are appended
to the evolver event log and exposed through `echo amplify gate` when a run
fails to meet the configured threshold.

## Storage & Manifest

* Snapshots append to `state/amplify_log.jsonl` using canonical JSON (`sort_keys`
  and rounded floats).
* Manifest updates land under `amplification.latest`, `amplification.rolling_avg`,
  and `amplification.gate`.  The pre-commit hook runs `echo amplify now --update-manifest`
  to keep the manifest in sync.

## CLI Quickstart

```
$ echo amplify now
$ echo amplify log --limit 5
$ echo amplify gate --min 72
$ echo forecast --cycles 12 --plot
```

`echo amplify now` prints a human summary, stable JSON payload, and SHA-256
digest.  Re-running the command without changing repository state yields the
same output, making it safe to script.

The `log` subcommand renders a rolling table with index deltas and emoji badges.
`gate` exits non-zero when the most recent index misses the threshold; the CI
workflow wires this to the `AMPLIFY_MIN` secret.  Forecast uses an AR/EMA blend
to project the next three indices and can render a Unicode sparkline for quick
visual inspection.

## How to Raise Your Index

* **Boost resonance:** run an additional emotional modulation pass and rebalance
  joy-to-rage ratios.
* **Refresh freshness:** tighten the cycle duration or rerun telemetry sweeps to
  reset the half-life curve.
* **Increase novelty:** evolve mythocode rules, mutate glyph scaffolds, and
  inject new propagation strategies.
* **Improve cohesion:** follow the recommended sequence end-to-end and ensure
  persistence steps complete.
* **Expand coverage:** awaken dormant entities and validate their statuses before
  closing the cycle.
* **Stabilise systems:** smooth CPU spikes, ensure orbital hops stay within the
  comfort band, and verify node counts.

## CI Troubleshooting

* If `echo amplify gate` fails in CI, inspect the nudge list printed alongside
  the failure message and rerun the cycle with targeted adjustments.
* Make sure `state/amplify_log.jsonl` is committed when new cycles are added so
  the rolling average reflects reality.
* When adjusting weights or thresholds, run `pytest -q tests/test_amplify_core.py`
  to confirm the deterministic guarantees still hold.

## MkDocs Card

For local MkDocs previews, add a card that streams the latest entries from
`state/amplify_log.jsonl` so the dashboard reflects live amplification data.
