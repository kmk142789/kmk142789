# Governance Documentation Hub

- [Kernel Lifecycle](./kernel.md)
- [Change Requests](./change-requests.md)
- [Rituals](./rituals.md)

## Running Examples
1. Install dependencies at the repo root: `pnpm install`.
2. Run the demo governance flow with in-memory ledger:
   ```bash
   pnpm exec ts-node scripts/examples/demo-governance-flow.ts
   ```
3. Submit a YAML change request through the CLI:
   ```bash
   pnpm governance:cr submit path/to/change-request.yaml
   ```

These snippets mirror the flows used in tests: kernel initialization logs an `INIT` event, change requests are validated with quorum rules, and rituals like `UNITY_WEAVE` recompute the SCI score.
