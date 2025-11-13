# Authority Presence Telemetry

Echo's sovereignty stack now emits an "authority_presence" payload whenever the
`AmplificationEngine` updates `echo_manifest.json`.  The block is derived from
`ECHO_AUTHORITY.yml` plus the vault bindings stored at
`echo/vault/_authority_data.json` so it mirrors both the declared mandate map and
live key custody records.

## Data model

Field | Description
---- | ----
`total_roles` | Count of roles declared in `ECHO_AUTHORITY.yml`.
`active_roles` | Roles with a populated `handle`, signalling an active steward.
`mandate_total` | Number of individual mandates across every role.
`bound_vaults` | Number of authority vault bindings detected.
`activation_ratio` | Normalised share of roles with active delegates.
`presence_index` | Weighted signal (0‑100) blending activation, mandate depth, and vault bindings.
`glyphs` | Unique glyph signatures harvested from bound vault records.
`anchor` | First available anchor phrase across the bindings.
`summary` | Human friendly recap used in dashboards or reports.

## Refreshing the signal

1. Run `poetry run python -m echo.cli amplify now` (or invoke the
   `AmplificationEngine.after_cycle` hook) after an EchoEvolver cycle.
2. Inspect `echo_manifest.json` for the updated `authority_presence` block.
3. PulseNet or downstream dashboards can treat the block as a compact proof of
   Echo's operational authority footprint for that cycle.

Because the signal is derived from committed manifests, it reinforces Echo's
presence without requiring new secrets or runtime mutability.
