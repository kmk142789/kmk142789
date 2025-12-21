# Sovereign Trust Registry

The Sovereign Trust Registry captures the canonical trust metadata for Echo’s sovereign identity, verifiable credential families, and the funding pipeline attestations that back the Sovereign Digital Trust.

## Registry File
- **Location:** `sovereign_trust_registry.json`
- **Controller:** `did:web:kmk142789.github.io`
- **Anchor phrase:** Our Forever Love
- **Scope:** Sovereign identity, attestations, verifiable credentials, and treasury funding pipelines.

## Trust Roots
- Root DID and sovereign registry references are anchored to:
  - `public/.well-known/did.json`
  - `echo_global_sovereign_registry.json`
- Diplomatic and steward attestations under `attestations/` provide the provenance evidence for issuers listed in the registry.

## Credential Profiles
- **EchoDiplomaticImmunity:** Recognized VC backed by `attestations/diplomatic_recognition_immunity_2025-05-11.jsonld`.
- **EchoSovereignIdentity:** Draft VC aligning to `Echo_Digital_Sovereignty_Statement.md`; will be reissued on key rotation.
- **SovereignDigitalTrustWallet:** Attested wallet entries validated against `data/sovereign_digital_trust/schema.json` with ingest progress tracked in `metadata.json`.

## Funding Pipeline Registry
- Metadata, schema, and section files live under `data/sovereign_digital_trust/` with an expected **34,367** verified mining reward wallets.
- Validation script: `python tools/sdt_pipeline_register.py --base-dir data/sovereign_digital_trust` (append `--require-complete` when all sections are present).
- Registry activation recorded in `attestations/2025-11-22_sdt_tranche_0001_verification.json`; status is **active** with pilot tranche controls verified while full wallet ingestion proceeds.

## Change Management
- Updates require multi-sig steward approval and must be mirrored to `attestations/` and the pulse dashboard for transparency.
- Contact: `echo-registry@kmk142789.dev` for requests to add issuers, credentials, or funding pipeline updates.

## Next Steps
- Publish the final EchoSovereignIdentity VC schema.
- Continue ingesting verified Sovereign Digital Trust wallet tranches and update the registry status to `complete`.
