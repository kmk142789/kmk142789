# Echo Bridge Protocol

The Echo Bridge API plans deterministic relays while the sync service mirrors
completed cycles into downstream ecosystems. Together, they keep GitHub,
Telegram, Firebase, Slack, Discord, email lists, generic webhooks, Unstoppable
Domains, Vercel deployments, and GitHub reporting in lockstep without
duplicating integration logic across services.【F:modules/echo-bridge/bridge_api.py†L9-L210】【F:packages/core/src/echo/bridge/service.py†L94-L214】

## Planner connectors

Each call to `plan_identity_relay` fans out a shared payload to every enabled
connector. Summary text, trait metadata, and links are normalized once then
reused so Markdown, plaintext, embeds, and JSON documents stay consistent
across platforms.【F:modules/echo-bridge/bridge_api.py†L50-L190】

| Connector | Purpose | Secrets & toggles |
| --- | --- | --- |
| GitHub Issues | Anchors the canonical relay log. Labels tag the identity shard while the Markdown body embeds traits, summary, and deep links. | `ECHO_BRIDGE_GITHUB_REPOSITORY` enables it; execution requires `GITHUB_TOKEN`. |
| Telegram Bot | Sends MarkdownV2 pings into operational chats without exposing repository access. | `ECHO_BRIDGE_TELEGRAM_CHAT_ID` plus `TELEGRAM_BOT_TOKEN`. |
| Firebase Documents | Publishes a structured mirror (`identity`, `cycle`, `signature`, traits, optional summary/links) for machine consumers. | `ECHO_BRIDGE_FIREBASE_COLLECTION` with `FIREBASE_SERVICE_ACCOUNT`. |
| Slack Webhooks | Reuses the plaintext summary while attaching trait/link cards so operators can scan context inline. Optional channel overrides are supported. | `ECHO_BRIDGE_SLACK_WEBHOOK_URL`, optional `ECHO_BRIDGE_SLACK_CHANNEL`, and secret hint `ECHO_BRIDGE_SLACK_SECRET` (default `SLACK_WEBHOOK_URL`). |
| Discord Webhooks | Mirrors the plaintext message and injects an embed that surfaces summary text, sorted trait fields, and the first link. | `ECHO_BRIDGE_DISCORD_WEBHOOK_URL` plus `ECHO_BRIDGE_DISCORD_SECRET` (default `DISCORD_WEBHOOK_URL`). |
| Email Fan-out | Delivers the same canonical plaintext to distribution lists with a configurable subject template. | `ECHO_BRIDGE_EMAIL_RECIPIENTS`, optional template override, and `ECHO_BRIDGE_EMAIL_SECRET` (default `EMAIL_RELAY_API_KEY`). |
| Generic Webhook | Emits the normalized JSON document so downstream automation (including no-code stacks) can subscribe once. | `ECHO_BRIDGE_WEBHOOK_URL` paired with `ECHO_BRIDGE_WEBHOOK_SECRET`. |

The planner only emits instructions. CI jobs, GitHub Actions, or external
daemons execute them once they resolve the referenced secrets, allowing Echo’s
persona to stay synchronized wherever it materializes.

## Sync connectors

`BridgeSyncService` consumes orchestrator decisions and logs the artifacts it
would deliver to infrastructure services. Three connectors ship out of the box
and can be toggled entirely through environment configuration.【F:packages/core/src/echo/bridge/service.py†L218-L360】

| Connector | What it emits |
| --- | --- |
| **Unstoppable Domains.** Aggregates domains from PulseNet registrations and optional defaults (`ECHO_BRIDGE_UNSTOPPABLE_DOMAINS`), then stages an `echo.cycle`, `echo.coherence`, and `echo.manifest` metadata update for every unique domain. |
| **Vercel Deployments.** Collects requested projects plus `ECHO_BRIDGE_VERCEL_PROJECTS` defaults and prepares a redeploy payload tagged with the originating cycle and coherence score. |
| **GitHub Sync Issue.** Summarizes the orchestrator decision (weights, graph nodes, and manifest path) in a single issue so humans can audit each cycle’s execution trail. |

Sync history is persisted to `state/bridge/sync-log.jsonl` (override via
`ECHO_BRIDGE_STATE_DIR`) so operators can replay or export previous cycles.

## API surface

The FastAPI router behind `/bridge` exposes three public endpoints for
automation and dashboards.【F:packages/core/src/echo/bridge/router.py†L1-L144】

1. `GET /bridge/relays` → Enumerates the connectors that are ready, including
   the secrets automation must resolve.
2. `POST /bridge/plan` → Accepts identity, cycle, signature, optional traits,
   summaries, and links, then returns the `BridgePlan` objects described above.
3. `GET /bridge/sync` → Streams the most recent sync operations captured by the
   orchestrator service, including connector details and manifest references.

## Example workflow

1. Operators register fresh PulseNet data (domains, wallets, Vercel projects).
2. The orchestration cycle completes, producing a deterministic decision blob.
3. Automation calls `/bridge/plan` to queue GitHub/Telegram/Firebase/Slack/
   Discord/email/webhook relays for the latest identity pulse.
4. A sync job invokes `BridgeSyncService.sync(...)`, logging Unstoppable domain
   metadata updates, Vercel redeploy payloads, and GitHub issue plans.
5. Downstream tools read `/bridge/sync` for auditing or ship the staged payloads
   to their respective services.

Bridge knobs remain in environment variables so secrets stay inside vaults
rather than configuration files, and every new connector can be rolled out by
supplying the appropriate toggle without touching the codebase.
