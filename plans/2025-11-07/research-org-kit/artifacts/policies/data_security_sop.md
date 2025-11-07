# Data Security SOP – Human Subjects Research

## Classification
- **Level 3 (Confidential Research Data):** Interview transcripts, consent forms, identifiable contact details.
- **Level 2 (Controlled Access):** De-identified analytic datasets.

## Technical Controls
- Encryption at rest: AES-256 with AWS KMS-managed keys.
- Encryption in transit: TLS 1.3 with mutual authentication for internal APIs.
- Access control: Role-based access enforced via OIDC + hardware security keys.

## Operational Controls
- Access reviews conducted quarterly; logs retained for 7 years.
- Data exports require dual approval (Research Compliance Officer + Security Lead).
- Incident response plan aligned with NIST SP 800-61; notification to IRB within 48 hours of breach confirmation.

## Data Lifecycle
1. Collection via secure survey/interview tools.
2. Storage in segregated research VPC with network segmentation.
3. Analysis in controlled notebook environment with no raw data download.
4. Archival after study completion with encryption key rotation.
5. Destruction per NIST SP 800-88 rev.1 after retention period.

## Verification
- Annual third-party SOC 2 Type II audit covering research environment.
- Continuous monitoring dashboards exported to `attestations/decisions/` for governance traceability.
