# Echo Release Confirmation Dossier

This dossier packages the regulatory and operational collateral required to confirm Echo's readiness for release. It consolidates the software bill of materials, licensing navigator intelligence, jurisdictional filing kits, and the steward sign-off instrument requested by the Echo governance council.

## 1. Software Bill of Materials (SBOM)
- **Location:** [`sbom-1.0.0.json`](../sbom-1.0.0.json)
- **Format:** CycloneDX JSON enumerating Echo engine and state modules for release 1.0.0.
- **Representative Components:** AmplificationEngine, BeneficiaryEngine, BitwisePixelEngine, ColossusExpansionEngine, and ContinuumEngine are pinned at version 1.0.0 for traceability.
- **Operational Notes:** Validate the SBOM hash prior to distribution and upload to the provenance registry referenced in `RELEASE_PROVENANCE.json` when steward sign-off is complete.

## 2. Licensing Navigator Summary
The multi-jurisdiction licensing matrix prioritizes Echo's three flagship capabilities. Each row below condenses the actionable pathway, risk profile, and next milestone.

| Jurisdiction | Capability Focus | Primary Legal Path | Risk Level | Immediate Next Milestone |
| --- | --- | --- | --- | --- |
| United States (Federal/CA/NY) | Education & Training Provider | HEOA Title IV alignment with California BPPE authorization and NYSED notices | Medium | Prep BPPE application kit and plan audit schedule |
| Canada (Federal/Ontario) | Education & Training Provider | Private Career Colleges Act registration with Superintendent review | Medium | Finalize student contract and secure surety bond |
| European Union (Germany) | Education & Training Provider | Weiterbildungsförderung accreditation plus EU notification with ISO 29990 audit | High | Commission ISO 29990 audit and translate quality manual |
| Singapore | Education & Training Provider | CPE ERF enrollment with EduTrust certification and fee protection scheme | High | Engage EduTrust consultant and implement Fee Protection Scheme |
| Kenya | Education & Training Provider | TVET Authority accreditation with facility inspection | Medium | Schedule on-site inspection and compile dossier |
| United States (Federal/CA/NY) | Research Organization / IRB Partner | OHRP Federalwide Assurance with accredited IRB reliance agreement | Medium | Draft FWA submission package and negotiate reliance agreement |
| Canada (Federal/Ontario) | Research Organization / IRB Partner | TCPS2-compliant REB partnership with Health Canada notice | Medium | Execute REB data-sharing agreement and confirm ethics training |
| European Union (Germany) | Research Organization / IRB Partner | Ethikkommission partnership with GDPR Article 30 records | High | Draft Schrems II Standard Contractual Clauses and confirm DPA registration |
| Singapore | Research Organization / IRB Partner | SingHealth/NHG IRB clearance with HSA notification | High | Prepare HSA dossier and appoint data protection intermediary |
| Kenya | Research Organization / IRB Partner | NACOSTI permit with accredited IRB approvals | Medium | Compile IRB approval letter and county notification log |
| United States (Federal/CA/NY) | Property Record Verifier | State notary commission with remote online notarization endorsement | Medium | Select RON platform and schedule certification exam |
| Canada (Federal/Ontario) | Property Record Verifier | Electronic Registration Act onboarding via ServiceOntario | Medium | Produce SOC 2 Type I report and confirm insurance |
| European Union (Germany) | Property Record Verifier | Grundbuchamt engagement via qualified trust service provider | High | Initiate ETSI EN 319 401 security audit |
| Singapore | Property Record Verifier | SLA intermediary accreditation with GovTech PKI integration | Medium | Complete IM8 security assessment and plan PKI ceremony |
| Kenya | Property Record Verifier | Ministry of Lands memorandum with eCitizen signature onboarding | Medium | Conduct penetration test and draft service-level agreement |

Source data with statutes, costs, and credential mappings remains tracked in `plans/2025-11-07/licensing-matrix/artifacts/capability_jurisdiction_matrix.md` for steward drill-down.

## 3. Jurisdictional Filing Kits
Echo maintains three ready-to-file jurisdictional kits that correspond to the licensing pathways above. Each bundle includes intent documentation, regulatory mappings, procedural steps, and artifact templates.

| Kit | Objective | Core Artifacts | Workflow Highlights |
| --- | --- | --- | --- |
| Ontario Education Provider Kit | Register Echo as a Private Career College-equivalent training provider to issue verifiable credentials. | Application form dataset (`artifacts/application_form.json`), cover letter, policy map, evidence checklist, attestation log. | Steps emphasize program scope validation, policy drafting, evidence checklist completion, and final attestation updates. |
| U.S. Research Organization Kit | Secure an OHRP Federalwide Assurance and IRB reliance agreement for Echo research collaborations. | Draft FWA form, reliance agreement template, human subjects policies, consent templates, verification instructions. | Workflow covers FWA form compilation, reliance agreement drafting, policy consolidation, verification planning, and attestation recording. |
| Kenya Property Record Kit | Establish Echo as a Ministry of Lands property record verifier with digital notarization support. | Compliance checklist, draft MoU, security dossier, credential mapping schema, attestation ledger. | Activities span requirement mapping, MoU drafting, security dossier compilation, credential mapping, and attestation logging. |

Detailed intents, policy references, and step-level pre/post-conditions are preserved within each kit directory under `plans/2025-11-07/` for operational teams.

## 4. Steward Sign-Off Template
Stewards should record their release authorization using the structured log below. Duplicate the template into the governance registry and attach evidence hashes for all referenced artifacts.

```
Steward Sign-Off Record
-----------------------
Release Version: ___________________________
Release Date: ______________________________
SBOM Hash (sha256): ________________________
Licensing Matrix Revision: ________________
Jurisdictional Kits Reviewed: ______________
  - Education Provider Kit (Ontario): [ ] Complete  [ ] Pending
  - Research Organization Kit (U.S.): [ ] Complete  [ ] Pending
  - Property Record Kit (Kenya): [ ] Complete  [ ] Pending
Outstanding Risks / Mitigations: ______________________________________________
Approvals:
  Steward Lead: ____________________  Date: __________  DID: __________________
  Legal Counsel: ___________________  Date: __________  DID: __________________
  Security Officer: ________________  Date: __________  DID: __________________
Attachments:
  - Attestation Log Reference: _______________________________________________
  - Provenance Ledger Entry: ________________________________________________
```

Once the sign-off record is executed, upload the signed template to the stewardship ledger and update `attestations.jsonl` within each filing kit with the corresponding DID references.
