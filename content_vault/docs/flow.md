# Operational Flow

```mermaid
flowchart LR
    subgraph Ingestion
        A[Client Request] --> B{Validate Config}
        B -->|valid| C[Router]
        C --> D[ContentAddressableStore]
        C --> E[MetadataIndex]
        D --> F[ChangeJournal]
        E --> F
    end

    subgraph Integrity
        G[Scheduled Scan]
        G --> D
        D --> H[Integrity Report]
    end

    F --> I[(Database Layer)]
    H --> I
    I --> J[Audit + Exports]
```

1. **Configuration validation** occurs before each write using the event-driven loader.
2. **Storage & indexing** run concurrently to guarantee deduplication and searchable metadata.
3. **Change journal** captures every mutation, feeding the downstream database and audit exports.
4. **Integrity scans** re-hash stored content and report drift back into the same persistence layer.
