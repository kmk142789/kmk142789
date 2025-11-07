# Steward Review Summary – Research Organization Kit

## Decision Needed
Approve the prepared OHRP FWA application and reliance agreement template for final legal review and submission.

## Components
- FWA form data in JSON and XML for e-file upload.
- Draft reliance agreement establishing roles with Bay Area Collaborative IRB.
- Human subjects protection plan, consent template, and data security SOP meeting 45 CFR 46 + HIPAA expectations.
- Verification playbook describing credential evidence and revocation triggers.

## Outstanding Requirements
- Finalize partnership with Bay Area Collaborative IRB and obtain their signature.
- Attach roster of engaged research protocols and investigator training certificates.
- Confirm HIPAA Business Associate Agreement (if PHI introduced) before submission.

## Approvals Requested
- ✅ Confirm selected IRB partner aligns with Echo risk appetite.
- ✅ Validate policy language for compliance with Belmont principles and ISO/IEC 27557 controls.
- ✅ Approve use of DID-based signatures for reliance agreement.

## Risks & Mitigations
- **Cross-border data transfers:** Use SCCs and update Data Security SOP if non-US storage required.
- **Credential issuance:** Ensure revocation automation triggers upon IRB suspension via status list webhook.

## Next Steps after Approval
1. Route documents to legal counsel and IRB counterpart for signature.
2. Submit FWA through OHRP electronic system with accompanying documents.
3. Record submission hash in `attestations.jsonl` and `attestations/decisions` ledger with steward DID signature.
