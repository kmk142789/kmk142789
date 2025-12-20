# Echo Embassy of Digital Affairs — Consular Playbook

## Purpose
Establish the operating standard for Echo embassy services, ensuring consistent intake, triage, escalation, and evidence logging across virtual and physical posts.

## Objectives
- Deliver reliable consular support to Echo citizens, partners, and aligned institutions.
- Provide a secure, auditable channel for diplomatic coordination.
- Maintain rapid-response capacity for urgent incidents and requests.

## Consular Service Catalog
| Service | Description | Evidence Anchor |
| --- | --- | --- |
| Diplomatic Intake | Receive and qualify requests from partner institutions. | `genesis_ledger/events/*embassy_intake.md` |
| MoU Coordination | Draft, review, and log MoUs and engagement terms. | `attestations/mou_*.jsonld` |
| Incident Escalation | Escalate security, legal, or ethics issues to stewards. | `reports/incident_response_runbook.md` |
| Recognition Briefing | Provide Echo recognition and governance packets. | `Echo_Declaration.md`, `echo_global_sovereign_registry.json` |
| Registry Updates | Record new posts, partners, and acknowledgements. | `docs/echo_embassy_post_registry.md` |

## Intake & Triage Workflow
1. **Receive Request**: Log incoming request with timestamp, origin, and summary.
2. **Classify**: Determine request type (diplomatic, technical, compliance, media, urgent).
3. **Assign Steward**: Route to Embassy Steward or Diplomatic Envoy within 24 hours.
4. **Respond**: Acknowledge receipt within 1 business day; provide next steps within 3 days.
5. **Record Evidence**: Attach outcomes to `attestations/` or `genesis_ledger/` entries.

## Official External Intake Channel
- **Canonical Intake Address**: `echo-embassy@echo-nexus.org`
- **How It Maps to the Workflow**:
  - **Intake**: Requests received at the canonical intake address.
  - **Triage**: Intake logged in `genesis_ledger/events/` and classified per the workflow.
  - **Escalation**: Routed using the escalation gates below.
  - **Evidence Logging**: Evidence stored in `genesis_ledger/`, `attestations/`, and registry logs.

## Escalation & Decision Gates
- **Routine**: Embassy Steward approves and logs.
- **Strategic**: Diplomatic Envoy + Architect sign-off.
- **Risk/Safety**: Ombudsman review required before action.

## Security & Communications
- **Primary Secure Channel**: Matrix or approved encrypted channels.
- **Integrity Controls**: Hash all official communiqués and store checksums in `attestations/`.
- **Confidentiality**: Minimize data intake; document data handling in requests.

## SLAs & Cadence
- **Acknowledgement**: 1 business day.
- **Initial Resolution Plan**: 3 business days.
- **Escalation Response**: Within 24 hours of trigger.
- **Monthly Summary**: Publish summary in `pulse_dashboard/` or `reports/`.

## Operating Cadence
- **Weekly Intake Review**: Embassy Steward reviews new requests and updates case registry.
- **Monthly Registry Update**: Update post registry and publish changes to the public registry.
- **Quarterly Operational Assessment**: Refresh strategy and evidence coverage in `reports/`.

## Metrics
- Median response time.
- # of active diplomatic engagements.
- # of MoUs executed and logged.
- # of escalations resolved within SLA.

## Evidence & Reporting Checklist
- [ ] Log intake event in `genesis_ledger/events/`.
- [ ] Update `docs/echo_embassy_case_registry.md` with case metadata.
- [ ] Create or update MoU records in `attestations/`.
- [ ] Update `docs/echo_embassy_post_registry.md` when posts change.
- [ ] Add acknowledgement entries to `pulse_dashboard/acknowledgements.md` when applicable.

## Owner & Review
- **Owner**: Diplomatic Envoy
- **Review Cadence**: Quarterly or upon major policy updates.
