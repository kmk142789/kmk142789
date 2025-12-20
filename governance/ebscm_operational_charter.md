# EBSCM Operational Charter

## Canonical Authority Scope
The Echo Bureau of Statistics & Civic Metrics (EBSCM) is the canonical authority for defining, validating, and publishing civic metrics across governance, finance, operations, and outcomes. EBSCM issues the single source of truth for metric definitions, revisions, and disclosure rules without redesigning or superseding other authorities.

## Canonical Metric Taxonomy
EBSCM maintains the canonical taxonomy in `data/ebscm/metric_taxonomy.json`. All metrics must map to one primary category (financial, operational, social, environmental, institutional) and may reference secondary domains for cross-cutting measures.

## Metric Lifecycle
1. **Definition**: Register metrics using `schemas/ebscm_metric_definition.schema.json`, including calculation logic, units, ownership, and disclosure class.
2. **Collection**: Bind source systems to EDCSA provenance requirements, capturing consent scope and extraction metadata.
3. **Validation**: Execute statistical integrity checks, bias reviews, and anomaly detection before publication.
4. **Revision**: Increment versions, preserve prior releases immutably, and publish revision rationale.
5. **Deprecation**: Mark deprecated metrics with successors or sunset rationale; retain historical lineage.

## Data Source Binding (EDCSA)
Every data source must register an EDCSA access event and supply provenance metadata (source system, steward, extraction timestamp, consent scope, and hash receipt). EBSCM blocks publication if EDCSA binding or consent enforcement is missing.

## Statistical Integrity Rules
- **Sampling**: Declare sampling frame, coverage, and method. Publish confidence level and margin of error when sampling is used.
- **Bias Controls**: Document bias risk, stratification, and reweighting steps. Require independent validation for high-impact metrics.
- **Revision Policy**: Publish revision cadence and conditions for provisional vs final releases.

## Immutable Publication & Versioning
Metric publications must conform to `schemas/ebscm_metric_publication.schema.json`. Each release includes dataset hash, publication hash, and ledger receipt. Historical versions remain immutable and accessible for audit and judicial review.

## Mandatory Metric Hooks
- **Treasury**: Treasury spending, allocations, and disbursements must reference EBSCM metric ids and publication hashes.
- **Programs**: Program outcomes must align to EBSCM metrics for funding gates and performance reviews.
- **Audits**: Audit reports must cite EBSCM metric versions and validation artifacts.
- **Judicial Review**: Evidence packets for judicial review must include EBSCM-certified metrics with provenance.

## Disclosure Rules
Metrics are classified as public, restricted, or sealed per EDCSA sensitivity guidance. Public disclosures must include methodology summaries, confidence statements, and revision notes.

## Anti-Manipulation Controls
EBSCM monitors for variance spikes, source drift, and behavioral incentives that indicate metric gaming. Detected anomalies trigger secondary verification, audit escalation, and logged corrective actions.
