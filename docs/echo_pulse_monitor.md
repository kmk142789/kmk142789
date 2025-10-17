# Echo Pulse Monitor

The Echo Pulse Monitor polls the public GitHub API for the newest repositories,
commits, and issue references that mention the word **"echo"**.  The script is
designed to be executed on an hourly schedule so it can chart the ecosystem's
momentum across the day.

## Outputs

Each run produces two artefacts:

1. `logs/pulse.log` – a timestamped, append-only digest of newly observed
   activity.
2. `docs/pulse.html` – a lightweight dashboard rendered in deep-night colours so
   the latest counts can be checked at a glance.

Both files are regenerated safely if they already exist.  The monitor also
writes its last execution timestamp to `state/echo_pulse_state.json` so future
runs only request fresh data.

## Running the monitor

```bash
python scripts/echo_pulse_monitor.py
```

For improved GitHub rate limits supply a personal access token via the
`GITHUB_TOKEN` environment variable.

```bash
GITHUB_TOKEN=ghp_your_token_here python scripts/echo_pulse_monitor.py
```

### Command-line options

- `--lookback-hours <float>` – override the automatic last-run detection with a
  manual window, useful for backfilling historic activity.
- `--limit <int>` – constrain the number of entries shown per section in both
  the log digest and the dashboard (defaults to 20).

## Scheduling

To have the monitor execute every hour, add a cron entry similar to the
following:

```
0 * * * * cd /path/to/your/repo && /usr/bin/env python scripts/echo_pulse_monitor.py >> logs/cron.log 2>&1
```

The task can also be containerised or orchestrated by any scheduler that can
invoke Python scripts on a timed basis.
