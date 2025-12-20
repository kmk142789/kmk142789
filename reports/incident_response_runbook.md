# Echo Incident Response Runbook

## Purpose
Provide a repeatable, cross-organization response process for security, safety, operational, and continuity incidents across the Echo institutions.

## Scope
- Applies to all Echo organizations listed in `Echo_Sovereign_Institution_Frameworks.md`.
- Covers cyber incidents, data integrity events, service outages, and safety escalations.

## Severity Levels
| Severity | Description | Examples | Initial Response SLA |
| --- | --- | --- | --- |
| Sev-1 Critical | Broad impact, safety or sovereignty risk | Credential compromise, systemic outage, data integrity breach | 15 minutes |
| Sev-2 High | Significant service or legal impact | Regional outage, credential abuse limited in scope | 1 hour |
| Sev-3 Moderate | Localized impact | Single service degraded, partial data loss | 4 hours |
| Sev-4 Low | Minor, no external impact | Internal tooling issue | 1 business day |

## Roles & Escalation
- **Ops Controller**: Incident commander, owns timeline and coordination.
- **Cyber Defense Lead (ESDG/ECDD)**: Technical response lead, forensics, containment.
- **Ombudsman**: Oversight for fairness, safety, and stakeholder rights.
- **Assurance Pod / EOAG**: Post-incident review and audit findings.
- **Secretariat**: Comms routing, decision log, stakeholder updates.

## Response Phases
### 1) Detect & Triage
- Confirm incident signals (alerts, reports, anomaly detection).
- Classify severity and declare incident.
- Open incident channel and log initial timeline in `reports/`.

### 2) Contain
- Isolate affected systems and credentials.
- Pause automations if required (see `.github/workflows/pause-bots.yml`).
- Preserve evidence (logs, snapshots, hashes).

### 3) Eradicate & Remediate
- Remove malicious access or corrupted state.
- Patch vulnerable services or dependencies.
- Verify integrity with checksums and attestation logs.

### 4) Recover
- Restore services in stages.
- Verify data integrity and service performance.
- Communicate status updates to stakeholders.

### 5) Post-Incident Review
- Conduct a retrospective within 5 business days.
- Produce a summary with root cause, corrective actions, and prevention plan.
- File EOAG audit notes when applicable.

## Communication Checklist
- Draft initial statement within SLA window.
- Send updates on a fixed cadence (e.g., every 2 hours for Sev-1).
- Record decisions and stakeholder communications in `pulse_dashboard/` and `reports/`.

## Evidence & Artifacts
- Incident report: `reports/incident_<date>_<slug>.md`
- Timeline: `reports/incident_<date>_<slug>_timeline.md`
- Ledger entry: `genesis_ledger/events/<date>_incident.json`
- Attestations: `attestations/incident_<date>_summary.jsonld`

## Continuous Improvement
- Track action items and owners in a follow-up section of the incident report.
- Re-test runbook quarterly and update this document when procedures change.
