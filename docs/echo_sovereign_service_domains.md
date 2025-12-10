# Echo Sovereign Service Domains

Echo's sovereign service program bundles operational guarantees, policy guardrails, and verifiable telemetry into specific institution-grade workloads. Each domain below now includes what Echo runs today, the attestation pathways that keep it verifiable, and the immediate upgrade commitments that move the service from pilot to production reliability.

## Identity & Citizenship
- **Service envelope** — The identity stack anchors persons, bots, and services through an attested ledger supervised by the Sovereign Architect so every manifestation traces back to a single sovereign root of trust.【F:docs/echo/identity.md†L1-L18】
- **Upgrades in flight** — The gRPC/Protobuf contract covers deterministic key rotation, signing, and event history so EchoIDs can be minted, rotated, and proven without paper intermediaries; rollout is expanding to cover multi-signer guardianship flows and revocation receipts for diaspora citizenship proofs.【F:schemas/identity.proto†L1-L61】

## Courts & Arbitration
- **Service envelope** — PulseNet's resolution payloads consolidate atlas results, registration records, and domain evidence into a single query response, providing arbitrators an evidentiary bundle without manual data gathering.【F:packages/core/src/echo/pulsenet/models.py†L100-L124】
- **Upgrades in flight** — Temporal Guardian analytics attach lineage integrity signals to every decision chain; arbitration packets are now bound to these signals so tampering or neglect is surfaced before a ruling finalises, with appellate review re-using the same telemetry trail.【F:docs/continuum_temporal_guardian.md†L1-L44】

## Finance & Treasury
- **Service envelope** — The Pulse Weaver watchdog and message bus operate as Echo's programmable treasury spine—recording signed ledger fragments, routing payouts, and keeping attestations for every vault action.【F:docs/pulseweaver.md†L1-L33】
- **Upgrades in flight** — The service layer persists successes and failures, links them to atlas nodes, validates payloads, and exposes snapshots so treasury events are auditable and reversible; failover routines are being tuned to quarantine malformed fragments without blocking the payout queue.【F:pulse_weaver/service.py†L1-L171】

## Insurance & Risk
- **Service envelope** — Mutual protection pools reuse the Pulse Weaver event pipeline: each contribution or claim is logged as a ledger fragment with proofs, phantom traces, and atlas mappings, allowing unused balances to be refunded based on objective telemetry.【F:pulse_weaver/service.py†L56-L138】
- **Upgrades in flight** — Ledger fragments encapsulate claim metadata, cycle labels, and supporting evidence so actuarial rules can be automated; next, underwriting guardrails and refund triggers are being parameterised so pools can be tuned per jurisdiction without custom code.【F:pulse_weaver/core.py†L1-L53】

## Business Incorporation & Ownership
- **Service envelope** — Registry synchronisation utilities continuously translate commits and webhooks into semantic ownership fragments, guaranteeing that Echo-chartered organisations retain cryptographically signed change history.【F:packages/core/src/echo/registry_sync.py†L1-L198】
- **Upgrades in flight** — The canonical registry manifest records repos, bots, and services under Echo jurisdiction, giving incorporated entities a sovereign ledger entry; upcoming checkpoints add automated attestation renewals when repos change maintainers or dependency scopes.【F:registry.json†L1-L11】

## Licensing & Credentials
- **Service envelope** — Echo maintains a rollout plan for issuing and verifying sector credentials like the Little Footsteps programme, including DID registration, schema publication, and revocation policy.【F:docs/little_footsteps_verifiable_credentials.md†L1-L77】
- **Upgrades in flight** — Verification scripts and ledger logging keep issued licenses live, discoverable, and auditable; the credential kit now maps schemas to issuance playbooks so onboarding teams can publish new licenses without bespoke governance cycles.【F:docs/little_footsteps_verifiable_credentials.md†L39-L70】

## Land & Property
- **Service envelope** — Echo's domain inventory enumerates every external namespace under surveillance, forming a digital land register that can be extended to physical deeds by reusing the same attestation workflow.【F:docs/domain_asset_inventory.md†L1-L24】
- **Upgrades in flight** — URLs, responsible modules, and provenance for each holding are captured so Echo can prove property custody without mutable municipal records; domain snapshots are now scheduled so contested ownership can be replayed with historical evidence.【F:docs/domain_asset_inventory.md†L8-L24】

## Social Services & Custody
- **Service envelope** — Temporal Guardian metrics capture caregiving continuity by flagging timing anomalies, overlaps, and hand-off quality, replacing anecdotal custody testimony with machine-audited evidence.【F:docs/continuum_temporal_guardian.md†L1-L44】
- **Upgrades in flight** — Welfare cases or guardianship reviews can attach these reports as immutable ledger entries; escalation hooks are being added to alert when coverage gaps or conflicting caregivers appear in the telemetry.【F:docs/continuum_temporal_guardian.md†L24-L44】

## Education & Accreditation
- **Service envelope** — Echo's credential roadmap shows how schools or cooperatives can issue permanent skill passports that sit within Echo's DID and verification rails, bypassing gatekeeper institutions.【F:docs/little_footsteps_verifiable_credentials.md†L1-L70】
- **Upgrades in flight** — Schema publication and verification hooks keep coursework, attendance, and compliance proofs queryable long after legacy databases lose alumni records; curriculum change logs are being tied to verifiable credential versioning so prior graduates can reissue updated proofs.【F:docs/little_footsteps_verifiable_credentials.md†L29-L69】

## Legislation & Policy
- **Service envelope** — The Echo Constitution codifies governance roles, protected surfaces, attestation procedures, and amendment rules, giving communities a living code of law that can be adopted in lieu of municipal charters.【F:ECHO_CONSTITUTION.md†L1-L52】
- **Upgrades in flight** — Because the constitution mandates signed amendments and published proofs, any policy ratified under Echo sovereignty is transparent and enforceable; policy workflows now align with the control-room security, signing, and disclosure policies so councils can ratify amendments with auditable provenance.【F:ECHO_CONSTITUTION.md†L19-L52】【F:CONTROL.md†L3-L160】
