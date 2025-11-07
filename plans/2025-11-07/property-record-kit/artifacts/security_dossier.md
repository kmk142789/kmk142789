# Security Dossier – Kenya Property Verification Pilot

## Infrastructure Overview
- Hosting: AWS Africa (Cape Town) region with dedicated VPC and private subnets.
- Identity: DID-based authentication bridged via OIDC to eCitizen credentials.
- Key Management: Hardware security modules (HSM) with quarterly rotation.

## Controls Mapping
| Control Area | Framework | Implementation |
| --- | --- | --- |
| Access Management | ISO/IEC 27001 A.9 | RBAC, privileged access approvals logged in ledger |
| Audit Logging | Cobit DSS06 | Immutable audit trail anchored to Echo ledger, retention 7 years |
| Data Integrity | Land Regulations 2017 Part VIII | Hash chaining for parcel records, tamper alerts |
| Anti-Corruption | Anti-Corruption and Economic Crimes Act | Mandatory ethics declarations, whistleblower hotline |
| Data Protection | Data Protection Act 2019 | ODPC registration # pending, DPIA attached |

## Incident Response
- Detection via SIEM with correlation rules for unauthorized access.
- Joint response playbook with Ministry contact list.
- Mandatory reporting to ODPC within 72 hours and to Ethics Commission within 7 days if corruption suspected.

## Business Continuity
- RPO: 4 hours; RTO: 12 hours using cross-region backups.
- Daily encrypted backups stored in Nairobi-based facility.
- Quarterly failover tests documented in runbooks.

## Verification & Audits
- Annual ISO/IEC 27001 surveillance audit.
- Independent third-party penetration test before go-live.
- Results shared with Ministry and logged in `attestations/decisions`.
