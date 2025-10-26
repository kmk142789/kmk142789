# Stakeholder Voice Programs

Lil Footsteps keeps parents and childcare providers in the loop through two
complementary governance programs. Their configuration is machine-readable so
every adjustment to the cadence or compensation is auditable.

## Parent Advisory Council

- **Charter:** quarterly council of nine parents who co-design services, review
  budgets, and nominate policy changes.
- **Compensation:** $250 stipend per meeting, childcare coverage on-site, and
  transit reimbursement for each participant.
- **Source:** [`state/parent_advisory_council.json`](../state/parent_advisory_council.json)
- **Summaries:** publish notes in `docs/parent_council_summaries/` within 72
  hours of each session.
- **Liaison:** council liaison escalates time-sensitive concerns directly to the
  Echo treasury stewards and ensures bilingual facilitation.

## Provider Feedback Loop

- **Office hours:** biweekly sessions hosted by the operations steward to cover
  payroll reconciliation, bulk purchasing updates, and training needs.
- **Surveys:** quarterly temperature checks with anonymized synthesis and
  follow-up actions shared publicly.
- **Shared services:** bulk purchasing co-op, legal hotline, and trauma-informed
  care training roadmap.
- **Source:** [`state/provider_feedback_loop.json`](../state/provider_feedback_loop.json)
- **Integration:** upcoming sessions appear in the Pulse dashboard via the
  `PublicImpactExplorer` dataset.

## Updating the programs

1. Amend the relevant JSON file with new meeting times, members, or services.
2. Run `python -m pulse_dashboard.builder` to refresh the dashboard dataset.
3. Commit both the JSON change and any published meeting summary for a complete
   audit trail.
