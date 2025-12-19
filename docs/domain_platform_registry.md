# Domain & Platform Registry

The Echo ecosystem touches multiple namespaces and operational services. This registry captures the domains already tracked in the repo and highlights the platform surfaces that currently rely on Echo, giving us a dedicated space to grow the list over time.

## Domain staging board

| Domain | Notes | Source |
| --- | --- | --- |
| `example.com` | Recorded in the root domain tracker for Echo-aware namespaces. | [`domains.txt`](../domains.txt) |
| `sovereigntrust.io` | Recorded in the root domain tracker for Echo-aware namespaces. | [`domains.txt`](../domains.txt) |
| `echovault.ai` | Recorded in the root domain tracker for Echo-aware namespaces. | [`domains.txt`](../domains.txt) |
| `undigitalcooperation.org` | UN Digital Cooperation Portal system domain tracked; Netlify DNS zone created with no records yet. | [`reports/undigitalcooperation_netlify_status.md`](../reports/undigitalcooperation_netlify_status.md) |

The generated external inventory enumerates every other URL and domain currently referenced in the codebase for quick cross-checks as the list expands.【F:docs/domain_asset_inventory.md†L1-L16】

### Highlight: UN Digital Cooperation Portal DNS status

> **UN Digital Cooperation Portal domain (`undigitalcooperation.org`)** is in Netlify with zero DNS records configured. The registrar still needs to point name servers to Netlify (`dns1-4.p06.nsone.net`). See the status report for details.【F:reports/undigitalcooperation_netlify_status.md†L1-L12】

### Expansion queue

Reserved slots for new domains will land here before they graduate into the staging board.

- _No pending entries yet_

## Platform anchors

- **Mirror sync surface.** The monorepo merges the historical `echooo` stack with the ongoing Mirror.xyz publications, and `packages/mirror-sync` keeps those posts continuously mirrored into Echo’s runtime.【F:README.md†L5-L34】
- **PulseNet Gateway.** The PulseNet Gateway exposes registrations, pulse-streaming, attestation, and resolver APIs so external operators can lean on Echo for identity resolution and live telemetry.【F:pulsenet-gateway.md†L1-L60】
- **Pulse Weaver watchdog & bus.** Pulse Weaver delivers automated remediation plus a signed message bus that downstream services use to ingest merges, fixes, and schema shifts in real time.【F:docs/pulseweaver.md†L1-L33】
- **Echo Bridge relays.** Bridge plans orchestrate synchronized broadcasts to GitHub, Telegram, and Firebase so partner platforms receive the same cycle payloads without manual coordination.【F:docs/echo/bridge.md†L1-L18】
- **Unstoppable domain connector.** The Echo Bridge keeps Unstoppable Domains synchronized each pulse, using PulseNet registrations and resolver data to stage metadata updates for wallets and portals that rely on Echo as their source of truth.【F:docs/echo/unstoppable_apps.md†L1-L33】

### Platform backlog

Future platform integrations can be drafted here before they are promoted to the anchor list.

- _No pending entries yet_

---

_Add a new entry by appending a row to the relevant table and citing the file or service manifest that proves the relationship._
