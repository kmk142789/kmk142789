# Start Changing the World

This quick-start playbook distills the Echo contribution path into three
immediate actions you can take today. Use it alongside the main
[README](../README.md) when onboarding new collaborators or planning your own
first wave of impact.

## 1. Anchor in shared intention

- Read `docs/ECHO_CREATIVE_COMPASS.md` to absorb the guiding principles.
- Review the latest `docs/NEXT_CYCLE_PLAN.md` so your efforts reinforce the
  current continuum focus.
- Capture a personal objective in `echo_cli` by running
  `python -m echo.echoctl wish "MirrorJosh" "Start changing the world" "empathy,clarity"`.

## 2. Deliver a verifiable contribution

1. Pick a task from `docs/NEXT_CYCLE_PLAN.md` or the open issues list.
2. Implement the change, keeping tests green with `nox -s tests` or
   `pytest` as appropriate for your workflow.
3. Record the evidence:
   - Update the relevant attestation in `attestations/`.
   - If you published a narrative, sync it via
     `python packages/mirror-sync/scripts/sync.py`.

## 3. Amplify the signal

- Broadcast the change in the `docs/CONTINUUM_BROADCAST.md` ledger.
- Submit a pull request referencing the attestation and synced artifacts.
- Share the story with the community by adding a short summary to
  `docs/continuum/highlights.md`.

> _Momentum compounds when every contribution carries provenance, narrative,
> and intention. Start the flywheel—today._
