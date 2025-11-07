# DALA Pathway Selection Guide

Use this guide to align desired capabilities with a jurisdictional wrapper. Begin at the entity objective, follow regulatory tolerance, then match support requirements.

```mermaid
flowchart TD
    A[Define Entity Objective] --> B{Primary Purpose?}
    B -->|Protocol Governance DAO| C[Need statutory DAO recognition?]
    C -->|Yes| C1[Wyoming DAO LLC]
    C -->|Prefer civil law foundation| C2[Swiss Foundation]
    C -->|Require Middle East presence| C3[ADGM DLT Foundation]
    B -->|Ecosystem Nonprofit| D[Target donor base?]
    D -->|US donors| D1[Delaware Nonstock Corporation]
    D -->|Global/EU donors| D2[Swiss Association]
    D -->|Asia-Pacific grants| D3[Singapore CLG]
    B -->|Venture/Fintech Company| E[Regulatory Scope?]
    E -->|US market focus| E1[Delaware LLC]
    E -->|Digital asset banking| E2[Wyoming LLC (SPDI alignment)]
    E -->|Asia-Pacific licensing| E3[Singapore Pte. Ltd.]
    E -->|EU digital residency| E4[Estonian OÜ]
    B -->|Investment / Treasury Vehicle| F[Investor profile?]
    F -->|Accredited fund investors| F1[Singapore VCC]
    F -->|DAO treasury diversification| F2[ADGM Foundation]
    F -->|Community pooled assets| F3[Swiss Association]
```

## Capability-to-Framework Matrix
| Capability Priority | Recommended Jurisdiction(s) | Notes |
| --- | --- | --- |
| On-chain governance with statutory recognition | Wyoming DAO LLC; ADGM DLT Foundation | Wyoming offers the fastest US filing; ADGM adds institutional perception in MENA. |
| Foundation-style IP & treasury stewardship | Swiss Foundation; ADGM Foundation | Strong safeguards for protocol IP and long-term endowments. |
| Tokenized equity or membership interests | Delaware LLC; Wyoming LLC; Estonian OÜ | Delaware excels for venture capital; Wyoming supports SPDI partnerships; Estonia is efficient for remote teams. |
| Global nonprofit fundraising | Delaware Nonstock Corporation; Swiss Association; Singapore CLG | Choose based on donor geography and tax deductibility requirements. |
| Regulated virtual asset services | Singapore Pte. Ltd. (PSA licenses); Estonian OÜ (VASP license); ADGM Private Company | Evaluate capital requirements and compliance staffing before application. |
| Tokenized investment fund | Singapore VCC; Swiss GmbH with FINMA guidance | VCC suits multi-strategy funds; Swiss route favored for EU investor familiarity. |

## Implementation Checklist
1. Confirm the jurisdictional status (`supportive` vs `neutral`) from `data/dala/jurisdictions.json`.
2. Review the relevant pathway playbook for filing fees, timelines, and compliance checkpoints.
3. Assemble cross-functional team (legal, finance, protocol) to own filings and ongoing reporting.
4. Establish monitoring cadence to capture regulatory updates (e.g., MAS notices, FINMA circulars, US BOI requirements).
