# Pulse Weaver Watchdog & Bus

The Pulse Weaver subsystem bundles a self-healing watchdog with a cross-repo
message bus.  The watchdog inspects failure events, executes a dry-run
remediation, and if successful applies the real fix.  Every run produces a
transcript under `state/watchdog_transcripts/` and persists proofs in
`state/watchdog_proofs/`.

The pulse bus emits signed JSON envelopes that capture merges, fixes, or schema
changes.  Messages are dropped into `state/pulses/outbox/` and optionally
forwarded to remote webhooks.  Inbound pulses are verified against registered
public keys and stored in `state/pulses/inbox/`.

## Configuration

- `ECHO_WATCHDOG_ENABLED` toggles automatic remediation.
- `ECHO_PULSE_INGEST_CAPACITY` / `ECHO_PULSE_INGEST_REFILL` adjust API rate
  limits.
- Signing keys live in JSON files with `key_id`, `private_key` and
  `public_key` entries.

## CLI

```
echo pulse watch --max-attempts 2 --cooldown-sec 30
echo pulse emit echo/example abc123 --kind fix --summary "Stabilise" --proof prf-1
```

## API

- `GET /pulse/health` – watchdog status
- `POST /pulse/repair` – trigger remediation cycle
- `POST /pulse/ingest` – ingest a signed pulse (rate limited)
