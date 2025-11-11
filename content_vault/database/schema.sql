-- Core relational schema for the content vault blueprint

CREATE TABLE IF NOT EXISTS vault_items (
    address TEXT PRIMARY KEY,
    content BLOB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS vault_metadata (
    address TEXT NOT NULL REFERENCES vault_items(address) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (address, key)
);

CREATE TABLE IF NOT EXISTS vault_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    reference TEXT NOT NULL,
    payload JSON,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_versions (
    version INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    checksum TEXT NOT NULL,
    metadata JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    role TEXT NOT NULL,
    capability TEXT NOT NULL,
    PRIMARY KEY (role, capability)
);
