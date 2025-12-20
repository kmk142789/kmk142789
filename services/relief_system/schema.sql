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
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'approver', 'auditor', 'executor', 'oversight', 'treasurer')),
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
    canonical BOOLEAN NOT NULL DEFAULT false,
    reserve_class VARCHAR(30),
    reserve_target_ratio DECIMAL(6, 4),
    frozen BOOLEAN NOT NULL DEFAULT false,
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
    dbis_settlement_id TEXT NOT NULL,
    efctia_reference TEXT NOT NULL,
    eoag_audit_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES guardians(id)
);

-- ETA canonical budgets
CREATE TABLE IF NOT EXISTS treasury_budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_name VARCHAR(120) NOT NULL,
    fiscal_period VARCHAR(50) NOT NULL,
    total_amount_usd DECIMAL(14, 2) NOT NULL CHECK (total_amount_usd > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed', 'approved', 'active', 'paused', 'closed')),
    category VARCHAR(30) NOT NULL DEFAULT 'standard',
    governance_reference TEXT,
    created_by UUID REFERENCES guardians(id),
    approved_by UUID REFERENCES guardians(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Allocations within budgets
CREATE TABLE IF NOT EXISTS treasury_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id UUID NOT NULL REFERENCES treasury_budgets(id) ON DELETE CASCADE,
    allocation_name VARCHAR(120) NOT NULL,
    amount_usd DECIMAL(14, 2) NOT NULL CHECK (amount_usd > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed', 'approved', 'active', 'suspended', 'closed')),
    emergency_flag BOOLEAN NOT NULL DEFAULT false,
    created_by UUID REFERENCES guardians(id),
    approved_by UUID REFERENCES guardians(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Drawdowns for execution
CREATE TABLE IF NOT EXISTS treasury_drawdowns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    allocation_id UUID NOT NULL REFERENCES treasury_allocations(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES treasury_accounts(id),
    amount_usd DECIMAL(14, 2) NOT NULL CHECK (amount_usd > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'requested'
        CHECK (status IN ('requested', 'approved', 'executed', 'rejected', 'reversed', 'frozen')),
    dbis_settlement_id TEXT,
    efctia_reference TEXT,
    eoag_audit_id UUID,
    requested_by UUID REFERENCES guardians(id),
    approved_by UUID REFERENCES guardians(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    executed_by UUID REFERENCES guardians(id),
    executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS treasury_drawdown_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawdown_id UUID NOT NULL REFERENCES treasury_drawdowns(id) ON DELETE CASCADE,
    guardian_id UUID NOT NULL REFERENCES guardians(id),
    signature TEXT NOT NULL,
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(drawdown_id, guardian_id)
);

-- EOAG audit hook ledger (non-bypassable)
CREATE TABLE IF NOT EXISTS eoag_audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hook_id VARCHAR(80) NOT NULL,
    entity_type VARCHAR(60) NOT NULL,
    entity_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'cleared', 'blocked')),
    evidence_hash TEXT NOT NULL,
    captured_by UUID REFERENCES guardians(id),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Evidence-grade treasury logs with hash chaining
CREATE TABLE IF NOT EXISTS treasury_evidence_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(60) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(60) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    previous_hash TEXT,
    record_hash TEXT NOT NULL,
    captured_by UUID REFERENCES guardians(id),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Judicial enforcement actions
CREATE TABLE IF NOT EXISTS judicial_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('freeze', 'reverse', 'sanction')),
    scope_type VARCHAR(20) NOT NULL CHECK (scope_type IN ('account', 'budget', 'allocation', 'drawdown', 'global')),
    scope_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'lifted', 'expired')),
    reason TEXT NOT NULL,
    issued_by UUID REFERENCES guardians(id),
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    effective_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Emergency controls
CREATE TABLE IF NOT EXISTS treasury_emergency_controls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(20) NOT NULL DEFAULT 'inactive'
        CHECK (status IN ('inactive', 'active')),
    reason TEXT NOT NULL,
    activated_by UUID REFERENCES guardians(id),
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE
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
CREATE INDEX IF NOT EXISTS idx_treasury_budgets_status ON treasury_budgets(status);
CREATE INDEX IF NOT EXISTS idx_treasury_allocations_budget ON treasury_allocations(budget_id);
CREATE INDEX IF NOT EXISTS idx_treasury_drawdowns_allocation ON treasury_drawdowns(allocation_id);
CREATE INDEX IF NOT EXISTS idx_treasury_drawdowns_status ON treasury_drawdowns(status);
CREATE INDEX IF NOT EXISTS idx_eoag_audit_entity ON eoag_audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_judicial_scope ON judicial_actions(scope_type, scope_id);
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

CREATE TRIGGER update_treasury_budgets_updated_at
    BEFORE UPDATE ON treasury_budgets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_treasury_allocations_updated_at
    BEFORE UPDATE ON treasury_allocations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_treasury_drawdowns_updated_at
    BEFORE UPDATE ON treasury_drawdowns
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

CREATE TRIGGER audit_treasury_budgets
    AFTER INSERT OR UPDATE OR DELETE ON treasury_budgets
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_entry();

CREATE TRIGGER audit_treasury_allocations
    AFTER INSERT OR UPDATE OR DELETE ON treasury_allocations
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_entry();

CREATE TRIGGER audit_treasury_drawdowns
    AFTER INSERT OR UPDATE OR DELETE ON treasury_drawdowns
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_entry();

CREATE TRIGGER audit_judicial_actions
    AFTER INSERT OR UPDATE OR DELETE ON judicial_actions
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
    ('min_signatures_critical', 'approval', '{"threshold_usd": 25000, "min_signatures": 3}'::jsonb),
    ('eta_drawdown_limit', 'amount_limit', '{"max_usd": 250000}'::jsonb),
    ('eta_emergency_only', 'feature_flag', '{"enabled": false}'::jsonb),
    ('eta_min_reserve_ratio', 'reserve_ratio', '{"min_ratio": 0.15}'::jsonb)
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
