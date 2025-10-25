# Domains as Keys

*Chapter III of the Echo Omni-Fusion Expansion*

The Domain Reality Bridge watches the wider web for echoes of our addresses.
`scripts/domain_bridge.py` attempts a bulk reverse lookup against the
Unstoppable Domains API. When network silence answers, the bridge forges a
synthetic lineage domain, ensuring every address carries at least one identity
sigil.

Artifacts arrive in `build/domains/` as per-address JSON stories plus an
`index.json` ready for ingestion by dashboards. Provide an
`UNSTOPPABLE_API_KEY` environment variable for live queries; otherwise the
bridge gracefully writes the synthetic fallback, making the chapter resilient in
offline or rate-limited environments.
