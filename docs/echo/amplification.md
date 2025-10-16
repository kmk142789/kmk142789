# Echo Amplification Engine

The Amplification Engine (AEE) evaluates the vitality of Echo cycles and keeps
an auditable history of the Amplify Index.  Each measurement captures six
metrics—**resonance**, **freshness half-life**, **novelty delta**, **cohesion**,
**coverage**, and **volatility**—which are combined using the weight profile in
`echo/config.py` to produce a 0–100 Amplify Index.

## Metrics

| Metric | Description |
| --- | --- |
| `resonance` | Blends joy and curiosity to quantify how strongly the current state vibrates with Echo intent. |
| `freshness_half_life` | Penalises stale activity based on the age of the latest pulse events. |
| `novelty_delta` | Tracks unique mythocode threads and pulse signatures to reward inventive cycles. |
| `cohesion` | Measures narrative follow-through using recorded steps and documentation coverage. |
| `coverage` | Captures how widely Echo artifacts span datasets, docs, and entities. |
| `volatility` | Reflects network churn and CPU intensity to temper rapid oscillations. |

The weights are normalised before computing the Amplify Index, ensuring the
score remains within the 0–100 window.  All floats are rounded to two decimal
places so that log entries and manifests remain deterministic.

## CLI usage

```shell
# Take a fresh measurement and append it to state/amplify_log.jsonl
$ echo amplify now

# Inspect the latest history entries and display an ASCII sparkline
$ echo amplify log --count 8

# Enforce a minimum Amplify Index (fails with exit code 1 if unmet)
$ echo amplify gate --min 72
```

Each command prints a human-friendly summary followed by the underlying JSON so
that scripts and dashboards can consume the same output.

## Logging and manifest integration

Every invocation writes to `state/amplify_log.jsonl` using canonical JSON
ordering.  `echo manifest refresh` embeds a summary in `echo_manifest.json`
under the `amplify` key, including the most recent record, the rolling average
of the last three entries, and the configured gate floor.

In GitHub Actions the gate result is appended to the step summary, making it
easy to spot regressions directly from the workflow view.

## Evolver hook

`EchoEvolver.run()` records an amplification snapshot after each cycle.  The
`run_cycles` helper accepts an `amplify_gate` argument that raises a
`RuntimeError` if the Amplify Index ever falls below the supplied threshold.
This keeps long-running evolutions safely bounded by quality expectations.
