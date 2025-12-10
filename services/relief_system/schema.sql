-- Relief System Database Schema (PostgreSQL)
-- Version: 1.1.0 - Hardened & production ready

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Administrators and approvers
CREATE TABLE IF NOT EXISTS guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    public_key TEXT,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'approver', 'auditor')),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret TEXT
);

-- Relief events - core ledger
CREATE TABLE IF NOT EXISTS relief_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amount_usd DECIMAL(12, 2) NOT NULL CHECK (amount_usd > 0),
    reason TEXT NOT NULL,
    beneficiary_id UUID,
    beneficiary_hint VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'disbursed', 'rejected', 'cancelled')),
    approved_by UUID REFERENCES guardians(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    disbursed_at TIMESTAMP WITH TIME ZONE,
    transaction_hash TEXT,
    signature TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Approval signatures - multi-sig support
CREATE TABLE IF NOT EXISTS approval_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    relief_event_id UUID NOT NULL REFERENCES relief_events(id) ON DELETE CASCADE,
    guardian_id UUID NOT NULL REFERENCES guardians(id),
    signature TEXT NOT NULL,
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(relief_event_id, guardian_id)
);

-- Treasury accounts
CREATE TABLE IF NOT EXISTS treasury_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('fiat', 'crypto', 'reserve')),
    balance_usd DECIMAL(12, 2) NOT NULL DEFAULT 0,
    address TEXT,
    institution VARCHAR(255),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Treasury transactions
CREATE TABLE IF NOT EXISTS treasury_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES treasury_accounts(id),
    transaction_type VARCHAR(20) NOT NULL
        CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer', 'fee')),
    amount_usd DECIMAL(12, 2) NOT NULL,
    balance_after DECIMAL(12, 2) NOT NULL,
    relief_event_id UUID REFERENCES relief_events(id),
    description TEXT,
    external_reference TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES guardians(id)
);

-- Governance rules
CREATE TABLE IF NOT EXISTS governance_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    rule_value JSONB NOT NULL,
    active BOOLEAN DEFAULT true,
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    effective_until TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES guardians(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log - immutable event log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    actor_id UUID REFERENCES guardians(id),
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Metrics snapshots
CREATE TABLE IF NOT EXISTS metrics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_date DATE NOT NULL UNIQUE,
    total_families_helped INTEGER NOT NULL DEFAULT 0,
    total_relief_disbursed_usd DECIMAL(12, 2) NOT NULL DEFAULT 0,
    total_events INTEGER NOT NULL DEFAULT 0,
    active_guardians INTEGER NOT NULL DEFAULT 0,
    treasury_balance_usd DECIMAL(12, 2) NOT NULL DEFAULT 0,
    metrics_detail JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_relief_events_status ON relief_events(status);
CREATE INDEX IF NOT EXISTS idx_relief_events_created_at ON relief_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_relief_events_approved_by ON relief_events(approved_by);
CREATE INDEX IF NOT EXISTS idx_treasury_transactions_account ON treasury_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_treasury_transactions_created ON treasury_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_signatures_event ON approval_signatures(relief_event_id);

-- ---------------------------------------------------------------------------
-- Functions & triggers
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_audit_entry()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        event_type,
        entity_type,
        entity_id,
        actor_id,
        action,
        old_values,
        new_values,
        ip_address,
        user_agent
    ) VALUES (
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        COALESCE(NEW.updated_by, OLD.updated_by),
        TG_OP,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        NULL,
        NULL
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update timestamps
CREATE TRIGGER update_guardians_updated_at
    BEFORE UPDATE ON guardians
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_relief_events_updated_at
    BEFORE UPDATE ON relief_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_treasury_accounts_updated_at
    BEFORE UPDATE ON treasury_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Audit critical tables
CREATE TRIGGER audit_relief_events
    AFTER INSERT OR UPDATE OR DELETE ON relief_events
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_entry();

CREATE TRIGGER audit_treasury_transactions
    AFTER INSERT OR UPDATE OR DELETE ON treasury_transactions
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_entry();

CREATE TRIGGER audit_governance_rules
    AFTER INSERT OR UPDATE OR DELETE ON governance_rules
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_entry();

-- ---------------------------------------------------------------------------
-- Default data
-- ---------------------------------------------------------------------------
INSERT INTO governance_rules (rule_name, rule_type, rule_value)
VALUES
    ('max_single_relief', 'amount_limit', '{"max_usd": 10000}'::jsonb),
    ('max_overhead_pct', 'percentage', '{"value": 0.05}'::jsonb),
    ('min_signatures_large', 'approval', '{"threshold_usd": 5000, "min_signatures": 2}'::jsonb),
    ('min_signatures_critical', 'approval', '{"threshold_usd": 25000, "min_signatures": 3}'::jsonb)
ON CONFLICT (rule_name) DO NOTHING;

-- Initial admin guardian (rotate immediately in production)
INSERT INTO guardians (username, email, password_hash, public_key, role)
VALUES (
    'admin',
    'admin@echodominion.org',
    '$2b$12$UgsJfYmj.DI3jZWU2cm/A.8/tS.Dnapb23iN5VAd5epyo.gyPcHba',
    'PLACEHOLDER_PUBLIC_KEY',
    'admin'
) ON CONFLICT (username) DO NOTHING;

COMMENT ON TABLE relief_events IS 'Core ledger of all relief distributions';
COMMENT ON TABLE audit_log IS 'Immutable audit trail of all system changes';
COMMENT ON TABLE governance_rules IS 'Dynamic governance parameters';
