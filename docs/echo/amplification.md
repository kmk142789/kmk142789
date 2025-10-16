# Echo Amplification Engine

The amplification engine measures the creative momentum of EchoEvolver
cycles.  Each cycle produces a deterministic **Amplify Snapshot** that
captures the headline metrics, a composite index, and the git commit hash
associated with the cycle.  Snapshots are written to
`state/amplify_log.jsonl` and summarised in `echo_manifest.json` under the
`amplification` key.

## Metrics

The engine derives six metrics from the evolver state:

| Metric | Description |
| ------ | ----------- |
| **Resonance** | Weighted blend of joy and the inverse of rage. |
| **Freshness half-life** | Exponential decay based on cycles since the last update. |
| **Novelty delta** | Mythocode breadth adjusted by emotional inputs. |
| **Cohesion** | Narrative and emotional alignment score. |
| **Coverage** | Percentage of recommended evolver steps executed. |
| **Stability** | Inverse of telemetry volatility. |

The composite index uses configurable weights:

```
index = w_r*resonance + w_f*freshness + w_n*novelty +
        w_c*cohesion + w_cov*coverage - w_s*volatility
```

where `volatility = 100 - stability`.  Default weights are defined in
`echo.amplify.AmplifyWeights` and can be tuned for bespoke deployments.

## Raising the Index

* **Boost resonance** by increasing joy inputs before each cycle.
* **Refresh freshness** with new prompts, datasets, or rule mutations.
* **Increase novelty** by expanding the mythocode library between cycles.
* **Strengthen cohesion** via narrative refactors and autonomy tuning.
* **Maximise coverage** by ensuring every recommended evolver step runs.
* **Protect stability** through telemetry audits and anomaly smoothing.

The engine emits nudges whenever a metric dips below the configured
thresholds (see `AmplifyThresholds`).  These appear in the evolver output
as `🔔 Amplify nudge` messages.

## CLI Workflow

```
echo amplify now       # compute latest snapshot (human + JSON)
echo amplify log       # inspect recent cycles
echo amplify gate --min 72  # fail if rolling average below 72
echo forecast --cycles 12 --plot  # blended AR/EMA projection
```

Running `echo amplify now` twice without code changes produces identical
JSON output; the engine reuses the existing timestamp when the metrics and
commit hash are unchanged.

## CI Troubleshooting

Continuous integration enforces `echo amplify gate --min 70`.  When the
gate fails:

1. Run `echo amplify log --limit 5` to inspect the trend.
2. Address the weakest metrics using the guidance above.
3. Regenerate the manifest (or re-run the evolver) to improve the index.
4. Commit the updated `state/amplify_log.jsonl` and `echo_manifest.json`.

For local safety, a pre-commit hook runs `echo amplify now` and refreshes
the manifest so that the amplification metadata stays in sync.
