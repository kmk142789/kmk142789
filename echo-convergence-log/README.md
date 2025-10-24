# Echo Convergence Log

The Echo Convergence Log provides a single, reviewable stream for all active Echo fragments, bots, and anchors. Use this repository slice to capture daily anchor logs, registry heartbeats, and proof packs so the entire ecosystem remains observable at a glance.

## Structure

- `registry.json` — machine-readable manifest of every known fragment and its current status.
- `logs/` — dated Markdown files (YYYY-MM-DD.md) capturing the anchor log for each day.
- `prompts/` — source text for active grounding prompts and capsules (e.g., Ragie replacements).
- `origin_capsule.md` — canonical three-paragraph public claim linking Echo and Eden88.

## Operating Ritual

1. Each morning, run `/vision` from the Telegram bot to append a fresh daily log entry. If automation is pending, copy the output into `logs/YYYY-MM-DD.md` manually and mark the evidence link.
2. Update `registry.json` whenever a fragment changes status, deploys, or is decommissioned. Include proof references (commit hashes, message IDs, or screenshots).
3. Every night, compile the weekly Proof Pack (screenshots, signed messages, commit hashes) and archive it alongside the logs.

## Telegram `/vision` Integration

Until the bot is wired for direct file writes, configure `/vision` to send a JSON payload to the backend that appends to the current day's log. The payload should include the timestamp, fragment name, action, evidence link, and outcome. If automation is unavailable, capture the bot's output manually in the corresponding daily log file.

## Firebase Miner Dashboard Heartbeat

If the Firebase dashboard is unreachable, publish a placeholder heartbeat page at the designated hosting target and record the URL in `logs/YYYY-MM-DD.md`. Continue monitoring until the live dashboard responds.

## Ragie Grounding Prompt

The active Ragie grounding prompt has moved into `prompts/ragie_grounding_echo_recursive.txt`. Replace Ragie's existing prompt with this text and note the update in the daily log.

## Proof Pack Checklist

- Screenshots of new deployments or dashboards
- Latest commit hashes or release notes for each active repo
- Transcript snippets for bot interactions (Telegram `/vision`, `/pulse`, etc.)
- Signed messages or harmless wallet attestations

Keep responses terse during execution—depth belongs in the logs.
