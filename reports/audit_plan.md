# Echo Office of the Auditor General — Audit Plan

## Purpose
Define the annual audit scope, cadence, and evidence expectations for Echo organizations.

## Audit Objectives
- Validate compliance with Echo governance, security, and signing policies.
- Confirm integrity of ledger, attestation, and registry artifacts.
- Ensure operational resilience and incident response readiness.

## Scope (Annual)
- All institutions listed in `Echo_Sovereign_Institution_Frameworks.md`.
- Core registries: `echo_global_sovereign_registry.json`, `registry.json`.
- Control policies: `CONTROL.md`, `SECURITY.md`, `SIGNING_POLICY.md`, `DISCLOSURE.md`.

## Audit Cadence
| Quarter | Focus | Key Outputs |
| --- | --- | --- |
| Q1 | Governance & policy controls | Governance gap report, remediation tracker |
| Q2 | Security & incident response readiness | IR tabletop review, security control validation |
| Q3 | Data integrity & registry consistency | Ledger parity report, registry reconciliation |
| Q4 | Financial stewardship & operational resilience | Treasury controls review, resilience assessment |

## Evidence Expectations
- Attestations in `attestations/` for all major decisions.
- Ledger entries in `genesis_ledger/events/` for incident and policy updates.
- Reports in `reports/` for audits, drills, and metrics.

## Reporting & Sign-off
- Draft reports prepared by Assurance Pod.
- Sign-off by EOAG and Ombudsman.
- Public summary released via `pulse_dashboard/`.

## Immediate Next Steps
1. Assign audit leads per quarter.
2. Publish the 12-month audit calendar.
3. Open remediation tracker in `reports/audit_remediation_tracker.md`.
