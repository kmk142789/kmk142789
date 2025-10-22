# PulseNet Gateway

The PulseNet Gateway turns the Continuum, Atlas, and Pulse subsystems into a
network-facing heartbeat layer. It combines four primary flows:

1. **Registration & Identity** – External operators and Echo fragments can
   register contact channels, wallets, and domain anchors. Registrations are
   persisted to `state/pulsenet/registrations.json` and surfaced through the
   `/pulsenet/register` and `/pulsenet/registrations` API endpoints.
2. **Pulse Activity Streaming** – Pulse history updates are tailed from
   `pulse_history.json` and broadcast to a `/pulsenet/pulse-stream` websocket.
   Each message contains the raw pulse, an attestation record, and a refreshed
   daily activity summary so listeners receive a live system heartbeat.
3. **Dynamic Attestation** – Every pulse is notarised into a temporal ledger at
   `state/pulsenet/temporal_ledger.jsonl`. The `/pulsenet/attestations` endpoint
   exposes recent entries as cryptographic proof-of-activity.
4. **Cross-Domain Resolution** – Atlas graph data, registrations, and optional
   resolver sources are merged to resolve wallets, Unstoppable domains, ENS
   names, and Vercel deployments under a single namespace via
   `/pulsenet/resolve`.

## API surface

| Endpoint | Description |
| --- | --- |
| `POST /pulsenet/register` | Register an identity with continuum / domain metadata. |
| `GET /pulsenet/registrations` | Return the stored registration ledger. |
| `GET /pulsenet/resolve?identifier=` | Resolve a name, wallet, or domain across Atlas and registrations. |
| `GET /pulsenet/attestations` | List the most recent pulse attestation entries. |
| `GET /pulsenet/summary` | Provide the current daily pulse summary snapshot. |
| `WS /pulsenet/pulse-stream` | Stream live pulses with attestation and summary payloads. |

## Configuration

* **Pulse history** – Reads from `pulse_history.json`. If the file is empty the
  gateway starts streaming as soon as new pulses arrive.
* **Ledger** – Uses `state/pulsenet/temporal_ledger.jsonl` for signed
  attestation events.
* **Resolver sources** – Optional hints can be stored in
  `state/pulsenet/resolver_sources.json` using the structure:

```json
{
  "Josh+Echo": {
    "unstoppable": ["josh.echo.crypto"],
    "ens": ["kmk142789.eth"],
    "vercel": ["pulsenet"],
    "wallets": ["0xABC..."]
  }
}
```

Registrations automatically extend the resolver, so the JSON hints are only
needed for static sources.

## Runtime embedding

`packages/core/src/echo/api/__init__.py` wires the gateway into the primary
FastAPI application, reusing the Atlas service, Pulse history, and state
filesystem. The unit tests in `tests/test_pulsenet_gateway.py` provide examples
of both API usage and websocket streaming.
