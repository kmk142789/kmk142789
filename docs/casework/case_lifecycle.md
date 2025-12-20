# Formal Case Lifecycle

This lifecycle standardizes how Echo casework is initiated, evaluated, resolved, and archived. Each stage maps to the allowed `status` values in `schemas/case.schema.json`.

## Lifecycle stages

| Stage | Entry criteria | Required outputs | Exit gate |
| --- | --- | --- | --- |
| **intake** | Intake logged with source summary and requestor | Intake record, intake ID, initial confidentiality flag | Triage owner assigned |
| **triage** | Intake accepted for review | Priority, classification, initial risk notes | Go/No-go decision recorded |
| **investigation** | Case accepted for deeper review | Evidence list, stakeholder map, preliminary findings | Decision forum scheduled |
| **deliberation** | Findings assembled | Draft decision memo, options, escalation notes | Decision authority signs off |
| **decision** | Decision authority selected | Decision summary, outcome reference, action plan | Implementation owner named |
| **implementation** | Action plan active | Execution checklist, progress updates, stakeholder comms | Completion review finished |
| **closed** | Implementation complete | Closure notes, outcome metrics, retrospective | Archive review scheduled |
| **archived** | Closure validated | Archive metadata, retention notes | Immutable log entry |

## Transition rules

- **intake → triage**: Intake owner assigns a triage team and confirms minimum information completeness.
- **triage → investigation**: Priority and classification are approved; any conflicts of interest are recorded.
- **investigation → deliberation**: Evidence inventory complete and findings distributed to decision forum.
- **deliberation → decision**: Decision authority issues a signed summary and outcome reference.
- **decision → implementation**: Action plan owner accepts execution responsibility and timeline.
- **implementation → closed**: Completion review verifies deliverables and stakeholder notice.
- **closed → archived**: Retention period and redaction requirements approved.

## Required ledger alignment

- Every stage transition MUST be represented in the case lifecycle history.
- Every decision or closure MUST include an outcome entry in `ledger/case_outcomes.jsonl`.
- Any re-opened cases return to **investigation** with a new lifecycle event.
