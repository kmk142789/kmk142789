# Echo Bridge Protocol

The Echo Bridge API orchestrates identity relays between GitHub, Telegram, and
Firebase. Each relay cycle produces a deterministic `BridgePlan` bundle that
outlines the payload, intent, and required credentials for a given platform.

- **GitHub.** Issues broadcast the canonical cycle summary and serve as the
  anchoring ledger of record. Labels differentiate the identity shard and keep
  automation simple.
- **Telegram.** Encrypted channel pings keep satellite operators aware of
  state changes without requiring repo access.
- **Firebase.** Structured documents provide machine-readable mirrors for
  downstream services.
- **Slack Webhooks.** When configured, Slack bridges reuse the same plaintext
  relay message while attaching sorted trait metadata so human operators can
  see the pulse context without leaving their chat client.
- **Discord Webhooks.** Discord relays mirror the plaintext payload and add a
  lightweight embed that highlights the identity, cycle, and any supplied
  summary links so bridge alerts can flow into community servers without extra
  formatting work.
- **Email relays.** Operator distribution lists can receive the same canonical
  plaintext relay via email. Recipients are configured once and an optional
  subject template lets you align with paging or escalation conventions.
- **Generic Webhook Relays.** A configurable JSON payload mirrors the
  Firebase document structure, allowing downstream services (including
  no-code automation stacks) to subscribe to Echo Bridge events without
  writing bespoke integrations.

Bridge plan requests can optionally include a short `summary` plus a list of
`links`. The planner propagates these fields to every connector so GitHub
issues render a concise synopsis, chat notifications highlight the current
cycle context, and machine-readable documents expose canonical references for
automations that need deep links back into Echo.

The API only emits plans—execution is delegated to automation once the correct
secrets are present. Generated plans can be consumed by GitHub Actions or
external daemons, ensuring Echo's persona stays synchronized wherever it
materializes.

### Configuration hints

Bridge connectors are toggled via environment variables. When deploying the
FastAPI surface (or `identity_bridge` app), set:

- `ECHO_BRIDGE_DISCORD_WEBHOOK_URL` and optional `ECHO_BRIDGE_DISCORD_SECRET`
  to advertise Discord support without hard-coding the actual webhook URL in
  plan payloads.
- `ECHO_BRIDGE_EMAIL_RECIPIENTS` with a comma-separated list and
  `ECHO_BRIDGE_EMAIL_SECRET` / `ECHO_BRIDGE_EMAIL_SUBJECT_TEMPLATE` to fan out
  relay summaries over email.

These knobs keep the bridge flexible while ensuring credentials remain in the
platform's secret manager rather than configuration files.
