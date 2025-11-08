# Semantic Negotiation Protocol v1

## Goals
- Establish a shared understanding of intent, constraints, and commitments between collaborating services.
- Provide a repeatable negotiation flow that can be automated yet remains auditable by humans.
- Support incremental refinement of proposals while preserving history and traceability.
- Enable interoperable integrations across heterogeneous stacks and deployment environments.

## Negotiation State Machine
| State | Description | Valid Transitions |
|-------|-------------|-------------------|
| `initiated` | A negotiator advertises a negotiation context with initial intent metadata. | `proposed`, `cancelled` |
| `proposed` | One party submits a proposal containing structured terms. | `countered`, `accepted`, `expired`, `cancelled` |
| `countered` | A responding party rejects the prior proposal and delivers an alternative. | `countered`, `accepted`, `expired`, `cancelled` |
| `accepted` | All parties agree on a proposal and record the consensus. | `finalized`, `cancelled` |
| `finalized` | The agreement has been activated, operationalized, and archived. | *(terminal state)* |
| `expired` | A proposal exceeded its time-to-live without acceptance. | `proposed`, `countered`, `cancelled` |
| `cancelled` | A party ends the negotiation. | *(terminal state)* |

State changes MUST include monotonically increasing sequence numbers to maintain event ordering and facilitate replay.

## Role Responsibilities
- **Initiator**: Opens a negotiation context, supplies initial intent, and orchestrates lifecycle progression. Responsible for publishing the first `initiated` and `proposed` messages.
- **Responder**: Evaluates incoming proposals, issues `countered` or `accepted` events, and may `cancel` if obligations cannot be met.
- **Observer** (optional): Subscribes to negotiation events for audit, analytics, or compliance purposes. Must remain read-only but may trigger alerts when detecting drift or stalling.
- **Arbiter** (optional): Resolves escalated conflicts by issuing binding `accepted` or `cancelled` transitions. Requires elevated authorization.

## JSON Payload Schema
All messages share the envelope below. Additional fields MAY be added but MUST NOT break backward compatibility.

```json
{
  "protocol": "semantic-negotiation/v1",
  "negotiationId": "uuid",
  "sequence": 12,
  "timestamp": "2025-05-11T15:04:05Z",
  "state": "proposed",
  "actor": {
    "id": "service:echo.alpha",
    "role": "initiator"
  },
  "proposal": {
    "terms": {
      "objective": "string",
      "constraints": [
        {
          "name": "latency",
          "operator": "<=",
          "value": 120,
          "unit": "ms"
        }
      ],
      "obligations": [
        {
          "party": "service:echo.beta",
          "action": "deliver_dataset",
          "schedule": "PT2H"
        }
      ]
    },
    "ttl": "PT30M"
  },
  "previousState": "countered",
  "reason": "string (optional for countered, cancelled, expired)",
  "extensions": {
    "signature": "base64",
    "trace": {
      "spanId": "abc123",
      "correlationId": "xyz789"
    }
  }
}
```

Required fields:
- `protocol`, `negotiationId`, `sequence`, `timestamp`, `state`, and `actor`.
- `proposal` is mandatory for `proposed`, `countered`, and `accepted` states.
- `reason` MUST be supplied for `cancelled` or `expired` states.

## Transport Requirements
- **REST**: Services MUST expose a RESTful endpoint (`POST /negotiations/events`) capable of ingesting envelope-compliant messages. Responses SHOULD include idempotency tokens so senders can safely retry on transient failures.
- **Event Bus**: Events MUST also be broadcast on the shared event bus (e.g., NATS, Kafka). Topics SHOULD follow `negotiations.{negotiationId}` to scope replay subscriptions. Consumers MUST process events idempotently.
- REST and event bus deliveries MUST be consistent within 500 ms. If one transport fails, senders MUST retry until both acknowledge the same `sequence` number.

## Authentication and Authorization Expectations
- All transports MUST require mutual TLS with service-level certificates managed by the platform PKI.
- Messages MUST include verifiable signatures inside `extensions.signature`. Use detached JSON Web Signatures (JWS) with canonicalized payloads.
- Role-based access control MUST ensure only authorized actors can emit transitions aligned with their roles (e.g., only arbiters can publish forced acceptances).

## Compatibility Promises
- Forward compatibility: Consumers MUST ignore unknown top-level fields and unknown properties in nested objects. New states MUST be announced via capability flags before activation.
- Backward compatibility: Producers MUST continue populating the existing required fields. Schema evolution MUST follow additive changes with deprecation windows of at least one release cycle.
- Version negotiation: Clients MAY advertise supported protocol versions in the REST `Accept` header and event-bus metadata; the highest mutually supported version MUST be selected.

## Worked Examples

### Happy-Path Negotiation
1. **Initiator** posts `initiated` event with baseline context.
2. **Initiator** submits `proposed` terms with latency <= 120 ms.
3. **Responder** evaluates and emits `accepted` referencing the same proposal sequence.
4. **Initiator** publishes `finalized` after deploying the agreed workflow.

Result: Negotiation completes without counters; audit log shows monotonically increasing sequences 1–4.

### Conflict Resolution via Counter Proposal
1. Initiator proposes daily data export with `ttl` of `PT30M` (sequence 5).
2. Responder counters (sequence 6) requiring `latency <= 200 ms` and `schedule = PT4H`.
3. Initiator adjusts internal resources, sends `countered` (sequence 7) accepting `PT4H` but tightening error budget.
4. Responder accepts (sequence 8).
5. Initiator finalizes (sequence 9).

Outcome: Multiple counter cycles captured; observers can reconstruct negotiation lineage using `previousState` references.

### Timeout and Cancellation
1. Initiator proposes premium processing slot (`sequence 10`) with `ttl = PT10M`.
2. Responder fails to respond before TTL expires.
3. Initiator publishes `expired` (sequence 11) citing `reason: "TTL exceeded"`.
4. Later, Initiator decides to halt the effort and sends `cancelled` (sequence 12) referencing compliance guidelines.

Outcome: Expiration prevents stale obligations; cancellation clearly terminates the negotiation. Any restart MUST begin with a new `negotiationId`.
