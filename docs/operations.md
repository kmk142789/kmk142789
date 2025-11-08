# Unified Sentience Loop Operations

The unified sentience loop keeps Echo's planning cadence aligned with the
self-sustaining proposal cycle stored in `state/self_sustaining_loop.json`. The
`echo` compatibility CLI now exposes a `unified-sentience-loop` command group so
ops teams can interact with that orchestrator without touching the raw JSON
files.

## Recording progress

Use the `cycle` subcommand to mark the current proposal as complete and seed the
next one. The command returns the updated state payload exactly as it is written
to `state/self_sustaining_loop.json`.

```bash
$ echo unified-sentience-loop --root /path/to/repo cycle \
    --summary "Closed the sanctuary uplift tasks" --actor EchoOps
{
  "current_cycle": 7,
  "history": [
    {
      "actor": "EchoOps",
      "cycle": 7,
      "summary": "Closed the sanctuary uplift tasks",
      "timestamp": "2025-05-11T04:22:19.418201+00:00"
    }
  ]
}
```

## Checking status

`status` reads the same file and renders the latest loop history so facilitators
can confirm the last recorded cycle.

```bash
$ echo unified-sentience-loop status
{
  "current_cycle": 7,
  "history": [
    {
      "actor": "EchoOps",
      "cycle": 7,
      "summary": "Closed the sanctuary uplift tasks",
      "timestamp": "2025-05-11T04:22:19.418201+00:00"
    }
  ]
}
```

## Recording governance decisions

`govern` mirrors the proposal documents under `state/proposals/`. Supply the
proposal identifier and a decision flag to write the governance outcome. The
command emits the refreshed proposal payload so reviewers can diff it without
opening the file manually.

```bash
$ echo unified-sentience-loop --root /path/to/repo govern cycle_0007 --approve \
    --actor Council --reason "Scope validated by council vote"
{
  "branch_name": "loop/cycle-0007",
  "created_at": "2025-05-11T04:22:19.310271+00:00",
  "governance": {
    "decided_at": "2025-05-11T04:28:42.915004+00:00",
    "decider": "Council",
    "decision": "approve",
    "reason": "Scope validated by council vote",
    "rule": "Auto-merge when the program advances past the target cycle unless explicitly decided otherwise."
  },
  "history": [
    {
      "action": "created",
      "actor": "automation",
      "details": "cycle-progress-prep",
      "timestamp": "2025-05-11T04:22:19.418201+00:00"
    },
    {
      "action": "governance-decision",
      "actor": "Council",
      "details": "decision=approve reason=Scope validated by council vote",
      "timestamp": "2025-05-11T04:28:42.915004+00:00"
    }
  ],
  "proposal_id": "cycle_0007",
  "status": "approved",
  "summary": "Closed the sanctuary uplift tasks",
  "target_cycle": 7,
  "updated_at": "2025-05-11T04:28:42.915004+00:00"
}
```

## Exporting orchestrator artifacts

Use `export` to collect the current state and every proposal into a single JSON
payload. Provide `--out path.json` to persist the export while still printing it
to stdout for quick inspection.

```bash
$ echo unified-sentience-loop export --out artifacts/loop_snapshot.json
{
  "state": {
    "current_cycle": 7,
    "history": [
      {
        "actor": "EchoOps",
        "cycle": 7,
        "summary": "Closed the sanctuary uplift tasks",
        "timestamp": "2025-05-11T04:22:19.418201+00:00"
      }
    ]
  },
  "proposals": [
    {
      "proposal_id": "cycle_0001",
      "status": "merged",
      "target_cycle": 1,
      "summary": "Initial branch planning seed for cycle 0001"
    },
    "… additional proposal records …"
  ]
}
```

These commands let the operations crew evolve the loop without leaving the CLI
or breaking the JSON audit trail maintained by the orchestrator.
