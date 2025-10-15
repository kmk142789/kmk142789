# Amplification Engine

The Amplification Engine measures creative momentum across Echo Evolver cycles and turns it into a single **Amplify Index**. Each snapshot is deterministic, timestamped with the active commit, and stored in `state/amplify_log.jsonl` for later inspection.

## Metrics

Every cycle produces a six-dimensional metric vector:

| Metric | Description |
| --- | --- |
| **Resonance** | Blends joy, curiosity, and controlled rage to capture the emotional charge of the cycle. |
| **Freshness half-life** | Tracks the volume of new events recorded in the cycle event log. More activity keeps ideas from going stale. |
| **Novelty delta** | Measures how far the mythocode diverges from the previous baseline, rewarding new rules and glyph mutations. |
| **Cohesion** | Rewards step completion and strong autonomy consensus. Incomplete orbital loops lower cohesion. |
| **Coverage** | Percentage of canonical cycle steps executed. Skipped steps immediately reduce coverage. |
| **Stability** | Normalises CPU utilisation, node counts, orbital hops, and process growth to penalise chaotic runs. |

The Amplify Index combines these metrics with the default weight profile

```
index = 0.22·resonance + 0.18·freshness + 0.18·novelty
        + 0.16·cohesion + 0.16·coverage - 0.10·volatility
```

where `volatility = 1 - stability`. The final index is scaled to 0–100.

## Snapshots and Storage

Each cycle produces an `AmplifySnapshot` containing the cycle number, metrics, index, RFC3339 timestamp, and commit SHA. Snapshots are appended to `state/amplify_log.jsonl` and summarised in `echo_manifest.json` under the `amplification` key (`latest`, `rolling_avg`, and `gate`).

The engine emits nudges whenever a metric falls below its threshold. Examples include:

- **Low novelty** → “mutate rule space with mythocode perturbation X”.
- **Cohesion drop** → “run refactor pass Y across the mythocode lattice”.
- **Coverage gap** → “replay unfinished orbital steps and seal the loop”.

Nudges appear in both the Evolver run log and the CLI output.

## Command Line

Run the Amplification CLI via the unified `echo` entrypoint:

```bash
echo amplify now        # print latest snapshot (human + JSON)
echo amplify log        # table of recent cycles with deltas and badges
echo amplify gate --min 72  # fail with non-zero exit if rolling index < threshold
echo forecast --cycles 12 --plot  # project next three cycles with ASCII sparkline
```

`echo amplify now` is deterministic for a given commit: repeated runs with no repository changes emit identical JSON payloads.

## Raising the Index

1. **Complete the loop.** Ensure every canonical cycle step executes; coverage and cohesion climb together.
2. **Refresh mythocode.** Inject new glyph combinations or autonomy signals when novelty dips.
3. **Balance the load.** Keep CPU usage, orbital hops, and process counts within the expected bands to stabilise volatility.
4. **Log deliberately.** Rich event logs extend the freshness half-life; empty logs decay quickly.

## Forecasting

`echo forecast` blends an exponential moving average with a short autoregressive trend to estimate the next three indices and reports a confidence band. Use the sparkline (`--plot`) to visualise momentum shifts during local MkDocs previews.

## CI Troubleshooting

The `echo-amplify` GitHub workflow runs the unit suite and enforces an Amplify gate (configured via the `AMPLIFY_MIN` repository secret). When CI fails:

1. Run `echo amplify log` locally to identify the weakest metrics.
2. Apply the suggested nudges (mutate mythocode, refactor steps, stabilise telemetry).
3. Re-run the Evolver cycle and commit the updated `amplify_log.jsonl` and `echo_manifest.json`.
4. Verify success with `echo amplify gate --min <threshold>` before pushing.

The pre-commit hook automatically runs `echo amplify now` and refreshes the manifest, keeping amplification state current in every change set.
