# DALA Lexicon Repository

The DALA Lexicon is the canonical, versioned repository for legal precedents, regulatory updates, and accreditation criteria that inform the Distributed Accreditation and Legal Alignment (DALA) program. Each entry is tracked with metadata to provide auditors, counsel, and operators with a single source of truth for compliance readiness.

## Repository Layout
- `precedents/` — Source opinions, supervisory guidance, and case law interpreted for DALA operations.
- `regulatory_updates/` — Statutes, rulemakings, and agency notices mapped to affected controls and domains.
- `accreditation/` — Accreditation standards, control catalogs, and readiness checklists linked to DALA evidence.
- `lexicon.json` — Machine-readable index summarizing all registered entries and their accreditation impact notes.
- `CHANGELOG.md` — Version log for curated updates and automated ingestion events.

## Versioning Strategy
- Semantic versioning (MAJOR.MINOR.PATCH) is applied to `lexicon.json` updates.
- Automated ingestion increments the patch number, while manual restructuring increments the minor or major number.
- The `CHANGELOG.md` file records every change with references to entry identifiers for traceability.

## Automated Ingestion
Use the `scripts/dala_lex_ingest.py` tool to add new authorities or updates. The script:
1. Parses the source document.
2. Generates accreditation impact notes based on the compliance domains outlined in `docs/dala/framework.md`.
3. Stores a structured JSON artifact in the appropriate subdirectory.
4. Updates `lexicon.json` with the new record and increments the repository version.
5. Appends a summary line to `CHANGELOG.md`.

## Manual Contributions
- Place supporting files (PDFs, raw notices, transcripts) alongside the generated JSON artifacts.
- Update `lexicon.json` and `CHANGELOG.md` manually only when bypassing the ingestion script for exceptional cases.
- Run `python scripts/dala_lex_ingest.py --help` for usage details.

## Accreditation Alignment
Every entry carries metadata that connects it to the four compliance domains:
1. Governance & Oversight
2. Fiduciary Duties & Financial Integrity
3. Data Protection & Privacy Operations
4. Cross-Border & Jurisdictional Alignment

Maintaining this repository ensures DALA accreditation packages can cite the latest legal authorities and demonstrate timely impact assessment.
