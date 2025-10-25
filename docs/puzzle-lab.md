# Puzzle Lab

Puzzle Lab provides a unified interface for exploring, verifying, and enriching the
`echo_map.json` catalogue. It ships as both a Streamlit dashboard and a Typer-based CLI
so that data exploration is just as comfortable in terminals as it is in browsers.

## Quickstart

```bash
# Regenerate the puzzle map and validate derivations
python -m echo_cli refresh
python -m echo_cli verify

# Explore interactively
streamlit run apps/puzzle_lab.py
```

### CLI reference

The CLI is exposed as `python -m echo_cli` or the `echo-puzzle-lab` entry point.

| Command | Purpose |
| --- | --- |
| `refresh` | Rebuild `echo_map.json` using the canonical orchestrator. |
| `verify` | Re-derive puzzle addresses, exiting non-zero on mismatches. |
| `stats` | Print summary metrics; `--build-charts` refreshes the PNG/SVG artefacts. |
| `enrich-ud` | Fetch Unstoppable Domains metadata for visible addresses (skips when creds absent). |
| `export` | Persist filtered rows to `exports/*.jsonl` via a pandas-style query. |

Use `-j/--json` (append it to the command, e.g. `python -m echo_cli stats -j`) to obtain
machine-readable output. Example export:

```bash
python -m echo_cli export --query "family=='P2PKH' and ud_bound==True" \
  --out exports/ud_p2pkh.jsonl
```

### Streamlit dashboard

Running `streamlit run apps/puzzle_lab.py` opens the Puzzle Lab dashboard. Key features:

* Sidebar filters for script family, UD binding, mismatch status, date range, and text search.
* Sticky table header with columns `Puzzle`, `Address`, `Family`, `Hash160`, `UD`, `PR`, `Status`.
* Detail drawer showing pkScript (ASM + hex), reconstruction notes, UD metadata, and lineage.
* Action buttons for UD enrichment, on-demand verification, JSONL export, and deep-link sharing.
* Auto-generated charts (bar, timeline, and UD coverage pie) saved to `reports/figures/` on load.

The charts double as documentation artefacts and are embedded in CI. They live at:

* `reports/figures/puzzle_lab_family.svg`
* `reports/figures/puzzle_lab_timeline.svg`
* `reports/figures/puzzle_lab_ud_coverage.svg`

PNG counterparts are still produced when you run `python -m echo_cli stats --build-charts`
or open the dashboard, but they are `.gitignore`d so the repository remains binary-free for
easier reviews.

## Unstoppable Domains (UD) enrichment

Puzzle Lab gracefully downgrades when UD credentials are missing. Set one of the following
variables to enable live lookups and caching in `.cache/ud/`:

* `UD_API_KEY`
* `UD_JWT`
* `UNSTOPPABLE_API_KEY` (legacy support)

When credentials are unavailable, both the CLI and dashboard display a muted info message
and skip enrichment while retaining all other functionality.

Network-driven tests and CI tasks automatically respect this behaviour, so the pipeline
remains green without secrets.

## Reproducible workflow

```bash
python -m echo_cli refresh
python -m echo_cli verify
streamlit run apps/puzzle_lab.py
```

Generated exports (`exports/*.jsonl`) and charts (`reports/figures/*`) are published as
workflow artefacts under **Puzzle Lab CI**.

## Screenshots & artefacts

The dashboard saves refreshed charts on load. Browse the following files for visual context:

* [`reports/figures/puzzle_lab_family.svg`](../reports/figures/puzzle_lab_family.svg)
* [`reports/figures/puzzle_lab_timeline.svg`](../reports/figures/puzzle_lab_timeline.svg)
* [`reports/figures/puzzle_lab_ud_coverage.svg`](../reports/figures/puzzle_lab_ud_coverage.svg)

For lineage deep links and export samples, inspect the `exports/` directory after using
`Export view` or the CLI `export` command.
