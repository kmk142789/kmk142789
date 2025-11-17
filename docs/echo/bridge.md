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
