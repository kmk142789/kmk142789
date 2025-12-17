# Echo Bridge Protocol

The Echo Bridge API plans deterministic relays while the sync service mirrors
completed cycles into downstream ecosystems. Together, they keep GitHub,
Telegram, Firebase, Slack, Discord, Bluesky, ActivityPub/Mastodon, email lists,
generic webhooks, DNS inventories, Unstoppable Domains, Vercel deployments,
Kafka streams, S3 archives, and GitHub reporting in lockstep without duplicating
integration logic across services.【F:modules/echo-bridge/bridge_api.py†L9-L294】【F:packages/core/src/echo/bridge/service.py†L94-L214】

## Planner connectors

Each call to `plan_identity_relay` fans out a shared payload to every enabled
connector. Summary text, trait metadata, and links are normalized once then
reused so Markdown, plaintext, embeds, and JSON documents stay consistent
across platforms.【F:modules/echo-bridge/bridge_api.py†L50-L200】 Priority hints
and topic tags travel with every connector; social relays convert topics into
hashtags while Slack/Discord/Matrix include them as structured fields for
filtering.【F:modules/echo-bridge/bridge_api.py†L230-L343】【F:tests/test_bridge_public_api.py†L19-L110】

| Connector | Purpose | Secrets & toggles |
| --- | --- | --- |
| GitHub Issues | Anchors the canonical relay log. Labels tag the identity shard while the Markdown body embeds traits, summary, and deep links. | `ECHO_BRIDGE_GITHUB_REPOSITORY` enables it; execution requires `GITHUB_TOKEN`. |
| Telegram Bot | Sends MarkdownV2 pings into operational chats without exposing repository access. | `ECHO_BRIDGE_TELEGRAM_CHAT_ID` plus `TELEGRAM_BOT_TOKEN`. |
| Firebase Documents | Publishes a structured mirror (`identity`, `cycle`, `signature`, traits, optional summary/links) for machine consumers. | `ECHO_BRIDGE_FIREBASE_COLLECTION` with `FIREBASE_SERVICE_ACCOUNT`. |
| Slack Webhooks | Reuses the plaintext summary while attaching trait/link cards so operators can scan context inline. Optional channel overrides are supported. | `ECHO_BRIDGE_SLACK_WEBHOOK_URL`, optional `ECHO_BRIDGE_SLACK_CHANNEL`, and secret hint `ECHO_BRIDGE_SLACK_SECRET` (default `SLACK_WEBHOOK_URL`). |
| Discord Webhooks | Mirrors the plaintext message and injects an embed that surfaces summary text, sorted trait fields, and the first link. | `ECHO_BRIDGE_DISCORD_WEBHOOK_URL` plus `ECHO_BRIDGE_DISCORD_SECRET` (default `DISCORD_WEBHOOK_URL`). |
| Bluesky Posts | Delivers the social relay text to a Bluesky account with optional link and tag metadata. | `ECHO_BRIDGE_BLUESKY_IDENTIFIER`, optional `ECHO_BRIDGE_BLUESKY_SERVICE`, and `ECHO_BRIDGE_BLUESKY_SECRET` (default `BLUESKY_APP_PASSWORD`). |
| Mastodon Status | Publishes a social-friendly status with hashtags derived from topics and optional links. | `ECHO_BRIDGE_MASTODON_INSTANCE`, optional `ECHO_BRIDGE_MASTODON_VISIBILITY`, and `ECHO_BRIDGE_MASTODON_SECRET` (default `MASTODON_ACCESS_TOKEN`). |
| ActivityPub Inbox | Sends a signed ActivityPub note to a configured inbox while retaining context tags. | `ECHO_BRIDGE_ACTIVITYPUB_INBOX`, optional `ECHO_BRIDGE_ACTIVITYPUB_ACTOR`, and `ECHO_BRIDGE_ACTIVITYPUB_SECRET` (default `ACTIVITYPUB_SIGNING_KEY`). |
| Matrix Room | Sends the social relay text into a Matrix room while tagging topics and priority for downstream routing. | `ECHO_BRIDGE_MATRIX_HOMESERVER`, `ECHO_BRIDGE_MATRIX_ROOM_ID`, and `ECHO_BRIDGE_MATRIX_SECRET` (default `MATRIX_ACCESS_TOKEN`). |
| Email Fan-out | Delivers the same canonical plaintext to distribution lists with a configurable subject template. | `ECHO_BRIDGE_EMAIL_RECIPIENTS`, optional template override, and `ECHO_BRIDGE_EMAIL_SECRET` (default `EMAIL_RELAY_API_KEY`). |
| Generic Webhook | Emits the normalized JSON document so downstream automation (including no-code stacks) can subscribe once. | `ECHO_BRIDGE_WEBHOOK_URL` paired with `ECHO_BRIDGE_WEBHOOK_SECRET`. |

The planner only emits instructions. CI jobs, GitHub Actions, or external
daemons execute them once they resolve the referenced secrets, allowing Echo’s
persona to stay synchronized wherever it materializes.

### Extended connectors

Echo Bridge also speaks to additional surfaces when their toggles are set:

- **Operational alerts.** PagerDuty, Opsgenie, and Statuspage payloads reuse the canonical relay body while mapping bridge priority to each tool’s severity taxonomy. Configure via `ECHO_BRIDGE_PAGERDUTY_*`, `ECHO_BRIDGE_OPSGENIE_*`, and `ECHO_BRIDGE_STATUSPAGE_*`.【F:modules/echo-bridge/bridge_api.py†L1747-L1824】
- **Social and community.** LinkedIn, Reddit, Farcaster, and Nostr publish social-friendly text with tags derived from bridge topics, keeping public surfaces in sync without reformatting content manually.【F:modules/echo-bridge/bridge_api.py†L1223-L1498】
- **Identity & domain anchors.** DNS TXT updates, Unstoppable Domain records, and Vercel redeploy triggers propagate cycle metadata to resolvers and static sites as soon as orchestration completes.【F:modules/echo-bridge/bridge_api.py†L1507-L1579】
- **Device and edge relays.** TCP, IoT, Wi‑Fi, and Bluetooth connectors emit the normalized bridge context over sockets, message buses, or broadcast frames so edge listeners receive the same payloads as cloud services.【F:modules/echo-bridge/bridge_api.py†L1579-L1698】
- **Documentation feeds.** Notion pages and RSS entries capture the rendered Markdown or plaintext body alongside traits, topics, and priority for knowledge bases and subscriber feeds.【F:modules/echo-bridge/bridge_api.py†L1465-L1746】
- **Data relays.** Kafka event payloads and S3 object writes persist the normalized bridge document for downstream stream processors or archival pipelines without reformatting per consumer.【F:modules/echo-bridge/bridge_api.py†L294-L356】

## Sync connectors

`BridgeSyncService` consumes orchestrator decisions and logs the artifacts it
would deliver to infrastructure services. Three connectors ship out of the box
and can be toggled entirely through environment configuration.【F:packages/core/src/echo/bridge/service.py†L218-L360】

| Connector | What it emits |
| --- | --- |
| **Domain inventory.** Reads tracked Web2 domains from `domains.txt` (override with `ECHO_BRIDGE_DOMAINS_FILE`) and optional static hints (`ECHO_BRIDGE_DOMAINS`), then prepares DNS anchor payloads annotated with the active cycle, coherence, and manifest path. |
| **Unstoppable Domains.** Aggregates domains from PulseNet registrations and optional defaults (`ECHO_BRIDGE_UNSTOPPABLE_DOMAINS`), then stages an `echo.cycle`, `echo.coherence`, and `echo.manifest` metadata update for every unique domain. |
| **Vercel Deployments.** Collects requested projects plus `ECHO_BRIDGE_VERCEL_PROJECTS` defaults and prepares a redeploy payload tagged with the originating cycle and coherence score. |
| **GitHub Sync Issue.** Summarizes the orchestrator decision (weights, graph nodes, and manifest path) in a single issue so humans can audit each cycle’s execution trail. |

Sync history is persisted to `state/bridge/sync-log.jsonl` (override via
`ECHO_BRIDGE_STATE_DIR`) so operators can replay or export previous cycles.

## API surface

The FastAPI router behind `/bridge` exposes three public endpoints for
automation and dashboards.【F:packages/core/src/echo/bridge/router.py†L1-L144】

1. `GET /bridge/relays` → Enumerates the connectors that are ready, including
   the secrets automation must resolve. Passing `include_sync=true` also lists
   orchestrator sync connectors (domain inventory, Unstoppable, Vercel, GitHub)
   so dashboards can surface both planning and replay capabilities in one call.
2. `POST /bridge/plan` → Accepts identity, cycle, signature, optional traits,
   summaries, and links, then returns the `BridgePlan` objects described above.
3. `GET /bridge/sync` → Streams the most recent sync operations captured by the
   orchestrator service, including connector details and manifest references.
   Supplying `?connector=github` (or any connector name) filters the results so
   dashboards can request focused history without transferring unrelated
   entries. Passing `include_stats=true` returns aggregate counts for the
   requested slice so operators can chart activity density without additional
   processing.【F:packages/core/src/echo/bridge/router.py†L150-L205】【F:packages/core/src/echo/bridge/service.py†L236-L297】
4. `POST /bridge/sync` → Executes a sync for a supplied decision payload, with
   optional connector filters, persists the operations, and returns both the
   emitted events and aggregate stats when requested.【F:packages/core/src/echo/bridge/router.py†L187-L205】

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
