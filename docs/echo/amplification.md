# Amplification Engine

EchoEvolver now ships with a first-class amplification engine that tracks the
creative pulse of every cycle.  The engine computes a blend of metrics,
persists a deterministic snapshot to `state/amplify_log.jsonl`, and updates the
root `echo_manifest.json` so downstream tooling can react instantly.

## Metrics

Each cycle records the following metrics on a `0‒100` scale:

| Metric | Description | Nudges |
| --- | --- | --- |
| `resonance` | Weighted mix of joy, curiosity, and inverse rage. | "Resonance dip: re-engage emotional modulation ritual X." |
| `freshness_half_life` | Exponential decay based on the elapsed time since the previous cycle. | "Freshness waning: schedule micro-retrospective cleanse." |
| `novelty_delta` | Jaccard-style delta between consecutive mythocode sets. | "Low novelty: mutate rule space with horizon drift set." |
| `cohesion` | Variance penalty across the emotional vector. | "Cohesion drop: run refactor pass Helix-Y." |
| `coverage` | Ratio of completed steps reported by `cycle_digest`. | "Coverage slump: rerun continue_cycle() with audit logging." |
| `stability` | Telemetry wobble derived from CPU, nodes, processes, and orbital hops. | "Stability wobble: recalibrate telemetry guardrails Z." |

The amplification index uses a tunable weight profile:

```
index = w_r·resonance + w_f·freshness + w_n·novelty + w_c·cohesion
        + w_cov·coverage - w_s·volatility
```

The default weights favour resonance while still rewarding complete cycles and
stable telemetry.  Volatility is simply `100 - stability`, so a calm system is
credited twice: once directly via stability and again by reducing the penalty
term.

## CLI

The CLI is exposed through `python -m echo`:

```bash
python -m echo amplify now                # Print the most recent snapshot
python -m echo amplify log --limit 5      # Table of recent cycles
python -m echo amplify gate --min 72      # Exit non-zero if below target
python -m echo forecast --cycles 12 --plot
```

`amplify now` prints a human summary followed by the canonical JSON payload.
Running it twice without new cycles yields an identical digest, making it safe
to gate commits or CI jobs.

`amplify log` computes deltas and badges (`🚀`, `✨`, `✅`, `⚠️`) so trend lines
are immediately visible.  When a metric falls below its threshold the engine
prints an auto-nudge in the evolver output and surfaces the same suggestion in
`amplify gate` failure messages.

The forecast command combines an exponentially weighted moving average with a
light AR(1) drift, produces projections for the next three cycles, and renders
an optional Unicode sparkline.  It intentionally caps confidence bands inside
`[0, 100]` so the forecast feels grounded on synthetic or sparse data.

## Raising the Index

* Re-run `continue_cycle()` to close out missing steps when coverage is low.
* Trigger `invent_mythocode()` or fresh creative inputs to boost novelty.
* Stabilise telemetry by rerunning `system_monitor()` or tuning RNG seeds.
* When resonance dips, bias `emotional_modulation()` toward higher joy values.

Manifest updates live under the `amplification` key:

```json
{
  "amplification": {
    "latest": 84.12,
    "rolling_avg": 82.47,
    "gate": 72.0
  }
}
```

This allows CI jobs, dashboards, or MkDocs cards to stream the latest index
without parsing the full log.

## CI troubleshooting

If `echo amplify gate` fails in CI:

1. Run `python -m echo amplify log` locally to inspect the cycle deltas.
2. Apply the suggested nudges (novelty mutations, cohesion refactors, etc.).
3. Re-run the evolver locally with `run_cycles` and commit the updated
   `state/amplify_log.jsonl` plus `echo_manifest.json`.
4. If the gate value should change, update the workflow secret
   `AMPLIFY_MIN` or pass a new `--min` to the CLI.

For MkDocs a simple card can read `state/amplify_log.jsonl` at runtime to show
the live table while developing locally.
