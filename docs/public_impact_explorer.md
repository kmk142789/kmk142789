# Public Impact Explorer

The Public Impact Explorer extends the Pulse Dashboard with end-to-end
transparency for Lil Footsteps. It combines real-time treasury activity,
childcare outcomes, and stakeholder voice updates so community members can
trace exactly how funds are raised, protected, and deployed.

## Data sources

The explorer aggregates the following canonical files:

| Signal | File | Description |
| ------ | ---- | ----------- |
| Nonprofit ledger | [`ledger/nonprofit_bank_ledger.json`](../ledger/nonprofit_bank_ledger.json) | Mirror of on-chain deposits and payouts. |
| Treasury policy | [`state/nonprofit_treasury_policy.json`](../state/nonprofit_treasury_policy.json) | Stablecoin targets, reserve balances, yield strategies, and emergency runway guardrails. |
| Impact metrics | [`reports/data/childcare_impact_metrics.json`](../reports/data/childcare_impact_metrics.json) | Families served, hours of care, caregiver wages, and equity analytics. |
| Parent voice | [`state/parent_advisory_council.json`](../state/parent_advisory_council.json) | Charter, membership, and meeting cadence for the Parent Advisory Council. |
| Provider voice | [`state/provider_feedback_loop.json`](../state/provider_feedback_loop.json) | Office hours, surveys, and shared services for childcare providers. |

All files are human-readable, version-controlled, and referenced in the
`PublicImpactExplorer` builder so the dashboard remains reproducible.

## Generating the dataset

Run the Pulse dashboard builder after updating any of the input files:

```bash
python -m pulse_dashboard.builder
```

The builder writes `pulse_dashboard/data/dashboard.json` with a
`public_impact_explorer` key that powers the new dashboard section.

## Key metrics

- **Treasury health:** aggregate deposits, payouts, ETH balance, and stablecoin
diversity score (target vs. actual allocation).
- **Emergency reserve:** shows whether the reserve meets the runway threshold and
highlights guardian controls.
- **Childcare outcomes:** rolling totals, cycle-specific highlights, equity
breakdowns by language and ZIP code, and job placement counts.
- **Stakeholder voice:** upcoming Parent Advisory Council sessions, provider
office hours, survey themes, and links to published summaries.

## Extending the explorer

1. Add new metrics or voices by appending to the relevant JSON files (for
example, add a `child_development` section under the impact metrics file).
2. Re-run the builder so the Pulse dashboard reflects the changes.
3. Update `docs/public_impact_explorer.md` with the new fields to keep the
explorer self-documenting.

Contributions should follow the transparency-first principle: every metric is
linked back to its raw ledger entries, survey outputs, or governance artefacts.
