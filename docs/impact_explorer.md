# Impact Explorer

The Impact Explorer extends the Echo Pulse dashboard with a transparency-first
view of the Lil Footsteps childcare treasury, community governance loops, and
operational safeguards. The dataset is generated from structured inputs in
`data/impact/` and published as part of `pulse_dashboard/data/dashboard.json`.

## Data sources

- **Financial events** (`data/impact/financial_events.json`): merged donation and
  disbursement records used to compute live balances, 30-day flow, and
  breakdowns by asset and funding source.
- **Impact metrics** (`data/impact/impact_metrics.json`): childcare outcomes,
  credentialing stats, and story highlights maintained by the operations team.
- **Community voice** (`data/impact/community_voice.json`): parent advisory
  council membership, meeting outcomes, and provider feedback programs.
- **Operations** (`data/impact/operations.json`): stablecoin strategy, wallet
  adoption, partnerships, sustainability levers, guardrails, resilience, legal
  posture, and culture rituals.

## Regenerating the dataset

```bash
python -m pip install -e .[dev]
python - <<'PY'
from pathlib import Path
from pulse_dashboard.builder import PulseDashboardBuilder

builder = PulseDashboardBuilder(project_root=Path('.').resolve())
print(builder.write())
PY
```

The resulting JSON document embeds the Impact Explorer block under the
`impact_explorer` key, ready for ingestion by the public dashboard.
