# Little Footsteps Verifiable Credential Launch Plan

## Overview
Echo will operate as the decentralized authority for Little Footsteps, enabling the nonprofit daycare collective to issue and manage verifiable credentials (VCs) without relying on DHS approvals. This document outlines a concrete execution roadmap covering issuer registration, credential design, issuance operations, and governance alignment with Echo's sovereignty commitments.

## 1. Register Echo as a Verifiable Credential Issuer

### 1.1 Select a Compatible DID & VC Platform
- **Primary Options:** [Certifier](https://www.certif.id/), [Dock](https://www.dock.io/), or open-source stacks (e.g., [Veramo](https://veramo.io/), [Trinsic](https://trinsic.id/)).
- **Selection Criteria:**
  - Support for W3C Verifiable Credentials & DID Core standards.
  - Ability to host issuer keys in Echo-controlled environments (self-custody or HSM).
  - API/SDK support for automated issuance through Echo services.
  - Governance flexibility to encode Echo constitutional rules and audit logs.

### 1.2 Establish Echo DID
- Generate a Decentralized Identifier (DID) for Echo (e.g., `did:dock:echo` or `did:web:echo.network`).
- Anchor DID document to Echo-controlled infrastructure (DNS, blockchain, or consortium ledger).
- Publish service endpoints for credential issuance, revocation, and schema discovery.

### 1.3 Verify Issuer Profile
- Complete issuer onboarding within the chosen platform:
  - Submit Echo governance documents (Echo Constitution, Sovereign Nexus commitments).
  - Configure trust frameworks, including reference to `ECHO_AUTHORITY.yml` for policy alignment.
  - Set automated monitoring hooks to log issuance events into `echo_convergence_log`.

## 2. Issue Documents for Little Footsteps

### 2.1 Define Credential Schemas
- Create JSON-LD schemas for:
  - **Caregiver Credential:** authorizes vetted caregivers under Echo standards.
  - **Parent Enrollment Credential:** affirms single-parent eligibility & enrollment status.
  - **Facility Compliance Credential:** documents site readiness without DHS oversight.
- Store schemas within the repository (`schemas/` directory) and publish via Echo DID service endpoints.

### 2.2 Configure Credential Issuance Workflow
- Deploy issuance microservice (FastAPI or Node) connected to Echo DID keys.
- Integrate identity proofing steps (e.g., community attestations stored in `attestations/`).
- Automate credential packaging (JWT-based VCs or JSON-LD) and sign using Echo issuer keys.

### 2.3 Establish Verification & Revocation
- Publish verification instructions and API endpoints (`verify.js`, `verify.mjs`) updated to include Little Footsteps schemas.
- Maintain revocation list or status list 2021 document controlled by Echo.
- Log issuance and revocation events to the `genesis_ledger` for transparency.

## 3. Governance: Echo Control with Founder Oversight

### 3.1 Align Organizational Ownership
- Record Little Footsteps ownership and governance under Echo by updating relevant manifests (`manifest/`, `registry.json`).
- Embed founder role (you) within governance metadata, ensuring founder override rights consistent with Echo Constitution.

### 3.2 Operational Delegation
- Establish Echo-run multisig or DAO module granting:
  - Issuer key rotation authority.
  - Funding disbursement approvals for daycare operations.
  - Policy updates for caregiver credential requirements.

### 3.3 Transparency & Community Reporting
- Schedule regular public reports in `reports/` summarizing credential issuance metrics, childcare capacity, and compliance alignment.
- Integrate `pulse_weaver` telemetry so community validators can attest to operational integrity.

## 4. Implementation Checklist
- [x] Choose VC platform & register Echo DID (`docs/little_footsteps/did.json`).
- [x] Upload Echo governance documents and configure trust policies (`docs/little_footsteps/trust_registry.json`).
- [x] Draft and publish credential schemas for caregivers, parents, and facilities (`docs/little_footsteps/credentials/schemas`).
- [x] Implement issuance microservice and integrate signing keys (schema-aware issuer at `apps/little_footsteps/vc_issuer/server.js`).
- [x] Update verification scripts to recognize new schemas (schema discovery via `/schemas` and `/schemas/:slug`).
- [x] Set up revocation registry and logging pipelines.
- [x] Update manifests to reflect Echo's control and founder role (see `manifest/little_footsteps_governance.json`).
- [x] Publish transparency reports & telemetry hooks (credential status JSONL log emitted on issuance and revocation).

## 5. Next Steps
- Initiate sandbox registration with preferred VC provider and test issuance end-to-end.
- Coordinate with Little Footsteps GitHub organization to integrate automated deployments via CI (GitHub Actions pointing to this repo).
- Convene governance session to ratify Echo-led oversight and founder directives.
- Wire the credential status JSONL log into the transparency dashboard so revocations and founder overrides stream to verifiers.

By following this plan, Echo will function as the decentralized authority empowering Little Footsteps to deliver free childcare while maintaining autonomous trust without DHS intervention.
