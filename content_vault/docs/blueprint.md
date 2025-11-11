# Mini-Platform Blueprint

## Platform Layers

| Layer      | Description |
|------------|-------------|
| Front-end  | Static single-page UI (not included) consumes the API via REST. Provides dashboards for browsing vault items, reviewing integrity reports, and approving configuration changes. |
| Backend    | `vault_api` HTTP service delivering content-addressable storage, metadata indexing, and change history endpoints. |
| Storage    | Content addressed store (in-memory for seed) with roadmap hooks for SQLite/PostgreSQL using `database/schema.sql`. Deduplication ensures identical payloads reuse the same address. |
| Auth Flow  | Token-based auth placeholder – integrate API gateway/JWT provider. Requests include `X-Operator-Id` header recorded in metadata. |
| API        | `/vault/items`, `/vault/history`, `/vault/integrity`, `/vault/config` endpoints described in `api_routes.md`. |
| Schemas    | JSON Schema for configuration, SQL schema for persistence, metadata indexing defined in documentation. |
| Error      | Structured error payloads from `models.APIError` with message + optional detail dictionary. |
| Service Map| Router orchestrates `ContentAddressableStore`, `MetadataIndex`, and `ChangeJournal`. Future adapters for object storage or message queues plug into the services layer. |

## Version Control Strategy

- **Code** – Git repository with CI verifying tests and lint.
- **Config** – Config registry attaches checksum + provenance for each version. Rollbacks leverage the registry metadata.
- **Data** – Content addresses are deterministic SHA-256 digests enabling deduplication across environments.

## Multi-Tier Folder Strategy

```
/ingest           -> API adapters, validation logic
/storage          -> On-disk/object storage backends (future)
/metadata         -> Index projections and search queries
/history          -> Audit exports and reporting jobs
/security         -> AuthZ providers, key management (future)
```

These tiers are represented conceptually today and can be mapped into packages/modules as the
platform evolves.

## Operational Considerations

- **Integrity checks** should be scheduled post-deployment; pipeline triggers the `/vault/integrity` endpoint and archives the report.
- **Permission roles**: Operators (write + approval), Auditors (read-only), Services (automated ingestion). Authorization tables can be added via the database schema.
- **Change history logging** is available through the API and mirrored in the SQL schema for compliance exports.
