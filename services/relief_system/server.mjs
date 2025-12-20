import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { body, param, validationResult } from 'express-validator';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';
import { Pool } from 'pg';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8080;

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'relief_system',
  user: process.env.DB_USER || 'relief_admin',
  password: process.env.DB_PASSWORD,
  max: 15,
  idleTimeoutMillis: 20_000,
  connectionTimeoutMillis: 5_000,
});

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;
const SIGNING_SECRET = process.env.SIGNING_SECRET || crypto.randomBytes(32).toString('hex');

if (!JWT_SECRET || !JWT_REFRESH_SECRET) {
  console.warn('[relief-system] JWT secrets are missing. Set JWT_SECRET and JWT_REFRESH_SECRET.');
}

app.use(helmet({
  crossOriginEmbedderPolicy: false,
  contentSecurityPolicy: {
    useDefaults: true,
    directives: {
      'default-src': ["'self'"],
      'style-src': ["'self'", "'unsafe-inline'"],
    },
  },
}));

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',').map((v) => v.trim()).filter(Boolean) || '*',
  credentials: true,
}));

app.use(express.json({ limit: '10kb' }));

const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
});

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  skipSuccessfulRequests: true,
});

app.use('/api', generalLimiter);
app.use('/api/auth', authLimiter);

function validateRequest(req, res, next) {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  return next();
}

async function createAuditLog(client, {
  eventType,
  entityType,
  entityId,
  actorId,
  action,
  oldValues = null,
  newValues = null,
  ipAddress = null,
  userAgent = null,
}) {
  await client.query(
    `INSERT INTO audit_log (event_type, entity_type, entity_id, actor_id, action, old_values, new_values, ip_address, user_agent)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
    [eventType, entityType, entityId, actorId, action, oldValues, newValues, ipAddress, userAgent],
  );
}

function signPayload(data) {
  const hmac = crypto.createHmac('sha256', SIGNING_SECRET);
  hmac.update(typeof data === 'string' ? data : JSON.stringify(data));
  return hmac.digest('hex');
}

function hashEvidence(payload) {
  const hash = crypto.createHash('sha256');
  hash.update(typeof payload === 'string' ? payload : JSON.stringify(payload));
  return hash.digest('hex');
}

async function authenticateToken(req, res, next) {
  const authHeader = req.headers.authorization;
  const token = authHeader?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    const guardianResult = await pool.query(
      'SELECT id, username, role, active FROM guardians WHERE id = $1',
      [payload.guardianId],
    );

    const guardian = guardianResult.rows[0];
    if (!guardian || !guardian.active) {
      return res.status(403).json({ error: 'Guardian inactive or missing' });
    }

    req.guardian = guardian;
    return next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token expired', code: 'TOKEN_EXPIRED' });
    }
    return res.status(403).json({ error: 'Invalid token' });
  }
}

function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.guardian || !roles.includes(req.guardian.role)) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: roles,
        current: req.guardian?.role,
      });
    }
    return next();
  };
}

async function getGovernanceRule(client, ruleName) {
  const result = await client.query(
    `SELECT rule_value FROM governance_rules
     WHERE rule_name = $1 AND active = true
     AND (effective_until IS NULL OR effective_until > CURRENT_TIMESTAMP)
     LIMIT 1`,
    [ruleName],
  );
  return result.rows[0]?.rule_value ?? null;
}

async function createEOAGAuditEvent(client, { hookId, entityType, entityId, status = 'pending', details, actorId }) {
  const evidenceHash = hashEvidence({ hookId, entityType, entityId, details, actorId, ts: new Date().toISOString() });
  const result = await client.query(
    `INSERT INTO eoag_audit_events (hook_id, entity_type, entity_id, status, evidence_hash, captured_by)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING id`,
    [hookId, entityType, entityId, status, evidenceHash, actorId],
  );
  return result.rows[0].id;
}

async function createEvidenceLog(client, { entityType, entityId, action, details, actorId }) {
  const previousResult = await client.query(
    `SELECT record_hash FROM treasury_evidence_log
     WHERE entity_type = $1
     ORDER BY captured_at DESC
     LIMIT 1`,
    [entityType],
  );
  const previousHash = previousResult.rows[0]?.record_hash || null;
  const recordHash = hashEvidence({ entityType, entityId, action, details, previousHash, actorId });
  await client.query(
    `INSERT INTO treasury_evidence_log (entity_type, entity_id, action, details, previous_hash, record_hash, captured_by)
     VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [entityType, entityId, action, details, previousHash, recordHash, actorId],
  );
  return recordHash;
}

async function ensureNoJudicialBlock(client, { scopeType, scopeId }) {
  const result = await client.query(
    `SELECT id, action_type, scope_type, scope_id
     FROM judicial_actions
     WHERE status = 'active'
     AND (scope_type = 'global' OR (scope_type = $1 AND scope_id = $2))`,
    [scopeType, scopeId],
  );
  if (result.rows.length) {
    return result.rows[0];
  }
  return null;
}

async function isEmergencyActive(client) {
  const result = await client.query(
    `SELECT status FROM treasury_emergency_controls
     WHERE status = 'active'
     ORDER BY activated_at DESC
     LIMIT 1`,
  );
  return result.rows.length > 0;
}

async function enforceReserveRatio(client, { deltaUsd = 0 }) {
  const minReserveRule = await getGovernanceRule(client, 'eta_min_reserve_ratio');
  const minRatio = Number(minReserveRule?.min_ratio ?? 0);
  if (!minRatio) {
    return { ok: true };
  }
  const result = await client.query(
    `SELECT
        COALESCE(SUM(balance_usd) FILTER (WHERE account_type = 'reserve'), 0) AS reserve_total,
        COALESCE(SUM(balance_usd), 0) AS total_balance
     FROM treasury_accounts
     WHERE active = true`,
  );
  const reserveTotal = Number(result.rows[0].reserve_total);
  const totalBalance = Number(result.rows[0].total_balance) + Number(deltaUsd);
  if (totalBalance <= 0) {
    return { ok: true };
  }
  const ratio = reserveTotal / totalBalance;
  if (ratio < minRatio) {
    return { ok: false, ratio, minRatio };
  }
  return { ok: true, ratio, minRatio };
}

// ---------------------------------------------------------------------------
// Authentication routes
// ---------------------------------------------------------------------------
app.post(
  '/api/auth/login',
  body('username').trim().notEmpty(),
  body('password').notEmpty(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      const { username, password } = req.body;
      const result = await client.query(
        'SELECT id, username, email, role, password_hash, active FROM guardians WHERE username = $1',
        [username],
      );

      const guardian = result.rows[0];
      if (!guardian || !guardian.active || !guardian.password_hash) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const passwordValid = await bcrypt.compare(password, guardian.password_hash);
      if (!passwordValid) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const accessToken = jwt.sign(
        { guardianId: guardian.id, role: guardian.role },
        JWT_SECRET,
        { expiresIn: '15m' },
      );

      const refreshToken = jwt.sign(
        { guardianId: guardian.id },
        JWT_REFRESH_SECRET,
        { expiresIn: '7d' },
      );

      await client.query('UPDATE guardians SET last_login = CURRENT_TIMESTAMP WHERE id = $1', [guardian.id]);

      await createAuditLog(client, {
        eventType: 'AUTH',
        entityType: 'guardian',
        entityId: guardian.id,
        actorId: guardian.id,
        action: 'LOGIN',
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
      });

      return res.json({
        accessToken,
        refreshToken,
        guardian: {
          id: guardian.id,
          username: guardian.username,
          email: guardian.email,
          role: guardian.role,
        },
      });
    } catch (error) {
      console.error('[relief-system] login error', error);
      return res.status(500).json({ error: 'Authentication failed' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/auth/refresh',
  body('refreshToken').notEmpty(),
  validateRequest,
  async (req, res) => {
    try {
      const { refreshToken } = req.body;
      const payload = jwt.verify(refreshToken, JWT_REFRESH_SECRET);

      const guardianResult = await pool.query(
        'SELECT id, role, active FROM guardians WHERE id = $1',
        [payload.guardianId],
      );

      const guardian = guardianResult.rows[0];
      if (!guardian || !guardian.active) {
        return res.status(403).json({ error: 'Invalid refresh token' });
      }

      const accessToken = jwt.sign(
        { guardianId: guardian.id, role: guardian.role },
        JWT_SECRET,
        { expiresIn: '15m' },
      );

      return res.json({ accessToken });
    } catch (error) {
      return res.status(403).json({ error: 'Invalid refresh token' });
    }
  },
);

// ---------------------------------------------------------------------------
// Relief routes
// ---------------------------------------------------------------------------
app.get('/api/governance/rules', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT rule_name, rule_type, rule_value, effective_from, effective_until
       FROM governance_rules
       WHERE active = true
       AND (effective_until IS NULL OR effective_until > CURRENT_TIMESTAMP)
       ORDER BY rule_name`,
    );
    return res.json({ rules: result.rows });
  } catch (error) {
    console.error('[relief-system] governance fetch error', error);
    return res.status(500).json({ error: 'Failed to fetch governance rules' });
  }
});

app.post(
  '/api/relief/request',
  authenticateToken,
  requireRole('admin', 'approver'),
  body('amount_usd').isFloat({ min: 0.01 }),
  body('reason').trim().isLength({ min: 10, max: 1000 }),
  body('beneficiary_hint').optional().trim().isLength({ max: 255 }),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');

      const { amount_usd, reason, beneficiary_hint } = req.body;

      const rulesResult = await client.query(
        `SELECT rule_value FROM governance_rules
         WHERE rule_name = 'max_single_relief' AND active = true`,
      );

      if (rulesResult.rows.length) {
        const maxAmount = Number(rulesResult.rows[0].rule_value?.max_usd);
        if (maxAmount && amount_usd > maxAmount) {
          await client.query('ROLLBACK');
          return res.status(400).json({
            error: 'Amount exceeds governance limit',
            max_allowed: maxAmount,
            requested: amount_usd,
          });
        }
      }

      const signature = signPayload({
        amount_usd,
        reason,
        beneficiary_hint,
        guardian_id: req.guardian.id,
        ts: new Date().toISOString(),
      });

      const insertResult = await client.query(
        `INSERT INTO relief_events (amount_usd, reason, beneficiary_hint, approved_by, signature, status)
         VALUES ($1, $2, $3, $4, $5, 'pending')
         RETURNING id, amount_usd, reason, status, created_at`,
        [amount_usd, reason, beneficiary_hint || null, req.guardian.id, signature],
      );

      const event = insertResult.rows[0];

      await createAuditLog(client, {
        eventType: 'RELIEF_REQUEST',
        entityType: 'relief_event',
        entityId: event.id,
        actorId: req.guardian.id,
        action: 'CREATE',
        newValues: event,
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
      });

      await client.query('COMMIT');

      return res.status(201).json({ success: true, event });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] relief request error', error);
      return res.status(500).json({ error: 'Failed to create relief request' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/relief/:id/approve',
  authenticateToken,
  requireRole('admin', 'approver'),
  param('id').isUUID(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;

      const eventResult = await client.query('SELECT * FROM relief_events WHERE id = $1 FOR UPDATE', [id]);
      const event = eventResult.rows[0];

      if (!event) {
        await client.query('ROLLBACK');
        return res.status(404).json({ error: 'Relief event not found' });
      }

      if (event.status !== 'pending') {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Event cannot be approved', current_status: event.status });
      }

      const rules = await client.query(
        `SELECT rule_value FROM governance_rules
         WHERE rule_name LIKE 'min_signatures%' AND active = true
         ORDER BY (rule_value->>'threshold_usd')::decimal DESC`,
      );

      let requiredSignatures = 1;
      for (const row of rules.rows) {
        const threshold = Number(row.rule_value?.threshold_usd || 0);
        if (Number(event.amount_usd) >= threshold) {
          requiredSignatures = Number(row.rule_value?.min_signatures || requiredSignatures);
          break;
        }
      }

      const signature = signPayload({ event_id: id, approver_id: req.guardian.id, ts: new Date().toISOString() });

      await client.query(
        `INSERT INTO approval_signatures (relief_event_id, guardian_id, signature)
         VALUES ($1, $2, $3)
         ON CONFLICT (relief_event_id, guardian_id) DO NOTHING`,
        [id, req.guardian.id, signature],
      );

      const signatureCountResult = await client.query(
        'SELECT COUNT(*)::int AS count FROM approval_signatures WHERE relief_event_id = $1',
        [id],
      );

      const signatureCount = signatureCountResult.rows[0].count;
      let newStatus = event.status;
      let approvedAt = event.approved_at;

      if (signatureCount >= requiredSignatures) {
        newStatus = 'approved';
        approvedAt = new Date();
        await client.query(
          `UPDATE relief_events SET status = $1, approved_at = $2, approved_by = $3, updated_at = CURRENT_TIMESTAMP
           WHERE id = $4`,
          [newStatus, approvedAt, req.guardian.id, id],
        );
      }

      await createAuditLog(client, {
        eventType: 'RELIEF_APPROVAL',
        entityType: 'relief_event',
        entityId: id,
        actorId: req.guardian.id,
        action: 'APPROVE',
        oldValues: { status: event.status },
        newValues: { status: newStatus, signature_count: signatureCount },
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
      });

      await client.query('COMMIT');

      return res.json({
        success: true,
        status: newStatus,
        signatures: { current: signatureCount, required: requiredSignatures },
        approved_at: approvedAt,
      });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] approval error', error);
      return res.status(500).json({ error: 'Failed to approve relief request' });
    } finally {
      client.release();
    }
  },
);

app.get('/api/relief/events', authenticateToken, async (req, res) => {
  try {
    const page = Math.max(Number(req.query.page) || 1, 1);
    const limit = Math.min(Math.max(Number(req.query.limit) || 20, 1), 100);
    const offset = (page - 1) * limit;
    const { status } = req.query;

    const params = [];
    let query = `
      SELECT re.*, g.username AS approved_by_username,
        (SELECT COUNT(*) FROM approval_signatures WHERE relief_event_id = re.id) AS signature_count
      FROM relief_events re
      LEFT JOIN guardians g ON re.approved_by = g.id
    `;

    if (status) {
      query += ' WHERE re.status = $1';
      params.push(status);
    }

    params.push(limit, offset);
    query += ` ORDER BY re.created_at DESC LIMIT $${params.length - 1} OFFSET $${params.length}`;

    const result = await pool.query(query, params);

    const countQuery = status ? 'SELECT COUNT(*)::int AS count FROM relief_events WHERE status = $1' : 'SELECT COUNT(*)::int AS count FROM relief_events';
    const countResult = await pool.query(countQuery, status ? [status] : []);
    const total = countResult.rows[0].count;

    return res.json({
      events: result.rows,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('[relief-system] events fetch error', error);
    return res.status(500).json({ error: 'Failed to fetch relief events' });
  }
});

// ---------------------------------------------------------------------------
// Treasury & metrics
// ---------------------------------------------------------------------------
app.get('/api/treasury/summary', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT account_type,
        COUNT(*) AS account_count,
        SUM(balance_usd) AS total_balance,
        COUNT(*) FILTER (WHERE canonical = true) AS canonical_count,
        SUM(balance_usd) FILTER (WHERE account_type = 'reserve') AS reserve_balance
       FROM treasury_accounts
       WHERE active = true
       GROUP BY account_type`,
    );
    return res.json({ summary: result.rows });
  } catch (error) {
    console.error('[relief-system] treasury summary error', error);
    return res.status(500).json({ error: 'Failed to fetch treasury summary' });
  }
});

// ---------------------------------------------------------------------------
// ETA Treasury Authority
// ---------------------------------------------------------------------------
app.post(
  '/api/eta/accounts',
  authenticateToken,
  requireRole('admin', 'treasurer'),
  body('account_name').trim().isLength({ min: 3, max: 100 }),
  body('account_type').isIn(['fiat', 'crypto', 'reserve']),
  body('balance_usd').optional().isFloat({ min: 0 }),
  body('canonical').optional().isBoolean(),
  body('reserve_class').optional().isLength({ max: 30 }),
  body('reserve_target_ratio').optional().isFloat({ min: 0 }),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const {
        account_name,
        account_type,
        balance_usd = 0,
        address,
        institution,
        canonical = false,
        reserve_class,
        reserve_target_ratio,
      } = req.body;

      if (canonical) {
        const existing = await client.query(
          'SELECT id FROM treasury_accounts WHERE canonical = true AND account_type = $1 AND active = true',
          [account_type],
        );
        if (existing.rows.length) {
          await client.query('ROLLBACK');
          return res.status(400).json({ error: 'Canonical account already set for type', account_type });
        }
      }

      const insertResult = await client.query(
        `INSERT INTO treasury_accounts
         (account_name, account_type, balance_usd, canonical, reserve_class, reserve_target_ratio, address, institution)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
         RETURNING *`,
        [
          account_name,
          account_type,
          balance_usd,
          canonical,
          reserve_class || null,
          reserve_target_ratio || null,
          address || null,
          institution || null,
        ],
      );

      const account = insertResult.rows[0];
      await createEOAGAuditEvent(client, {
        hookId: 'treasury-transaction-hook',
        entityType: 'treasury_account',
        entityId: account.id,
        details: account,
        actorId: req.guardian.id,
      });
      await createEvidenceLog(client, {
        entityType: 'treasury_account',
        entityId: account.id,
        action: 'CREATE',
        details: account,
        actorId: req.guardian.id,
      });
      await createAuditLog(client, {
        eventType: 'TREASURY_ACCOUNT',
        entityType: 'treasury_account',
        entityId: account.id,
        actorId: req.guardian.id,
        action: 'CREATE',
        newValues: account,
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
      });

      await client.query('COMMIT');
      return res.status(201).json({ account });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta account error', error);
      return res.status(500).json({ error: 'Failed to create treasury account' });
    } finally {
      client.release();
    }
  },
);

app.get('/api/eta/accounts', authenticateToken, async (_req, res) => {
  try {
    const result = await pool.query(
      `SELECT * FROM treasury_accounts WHERE active = true ORDER BY created_at DESC`,
    );
    return res.json({ accounts: result.rows });
  } catch (error) {
    console.error('[relief-system] eta accounts fetch error', error);
    return res.status(500).json({ error: 'Failed to fetch treasury accounts' });
  }
});

app.post(
  '/api/eta/budgets',
  authenticateToken,
  requireRole('admin', 'approver', 'treasurer'),
  body('budget_name').trim().isLength({ min: 3, max: 120 }),
  body('fiscal_period').trim().isLength({ min: 3, max: 50 }),
  body('total_amount_usd').isFloat({ min: 0.01 }),
  body('category').optional().isIn(['standard', 'crisis']),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const emergencyActive = await isEmergencyActive(client);
      const { budget_name, fiscal_period, total_amount_usd, category = 'standard', governance_reference } = req.body;

      if (emergencyActive && category !== 'crisis') {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Emergency controls active: only crisis budgets allowed' });
      }

      const insertResult = await client.query(
        `INSERT INTO treasury_budgets
         (budget_name, fiscal_period, total_amount_usd, category, governance_reference, created_by)
         VALUES ($1, $2, $3, $4, $5, $6)
         RETURNING *`,
        [budget_name, fiscal_period, total_amount_usd, category, governance_reference || null, req.guardian.id],
      );
      const budget = insertResult.rows[0];
      await createEOAGAuditEvent(client, {
        hookId: 'governance-decision-hook',
        entityType: 'treasury_budget',
        entityId: budget.id,
        details: budget,
        actorId: req.guardian.id,
      });
      await createEvidenceLog(client, {
        entityType: 'treasury_budget',
        entityId: budget.id,
        action: 'PROPOSE',
        details: budget,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.status(201).json({ budget });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta budget error', error);
      return res.status(500).json({ error: 'Failed to create budget' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/budgets/:id/approve',
  authenticateToken,
  requireRole('admin', 'oversight'),
  param('id').isUUID(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;

      const block = await ensureNoJudicialBlock(client, { scopeType: 'budget', scopeId: id });
      if (block) {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Judicial enforcement active', block });
      }

      const result = await client.query(
        `UPDATE treasury_budgets
         SET status = 'approved', approved_by = $1, approved_at = CURRENT_TIMESTAMP
         WHERE id = $2 AND status = 'proposed'
         RETURNING *`,
        [req.guardian.id, id],
      );
      const budget = result.rows[0];
      if (!budget) {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Budget not found or already approved' });
      }
      await createEOAGAuditEvent(client, {
        hookId: 'governance-decision-hook',
        entityType: 'treasury_budget',
        entityId: budget.id,
        status: 'cleared',
        details: { approved_by: req.guardian.id },
        actorId: req.guardian.id,
      });
      await createEvidenceLog(client, {
        entityType: 'treasury_budget',
        entityId: budget.id,
        action: 'APPROVE',
        details: budget,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.json({ budget });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta budget approve error', error);
      return res.status(500).json({ error: 'Failed to approve budget' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/budgets/:id/allocations',
  authenticateToken,
  requireRole('admin', 'approver', 'treasurer'),
  param('id').isUUID(),
  body('allocation_name').trim().isLength({ min: 3, max: 120 }),
  body('amount_usd').isFloat({ min: 0.01 }),
  body('emergency_flag').optional().isBoolean(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;
      const { allocation_name, amount_usd, emergency_flag = false } = req.body;

      const budgetResult = await client.query('SELECT * FROM treasury_budgets WHERE id = $1', [id]);
      const budget = budgetResult.rows[0];
      if (!budget) {
        await client.query('ROLLBACK');
        return res.status(404).json({ error: 'Budget not found' });
      }

      const emergencyActive = await isEmergencyActive(client);
      if (emergencyActive && !emergency_flag && budget.category !== 'crisis') {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Emergency controls active: crisis allocation required' });
      }

      const allocationSumResult = await client.query(
        `SELECT COALESCE(SUM(amount_usd), 0) AS allocated
         FROM treasury_allocations
         WHERE budget_id = $1`,
        [id],
      );
      const allocated = Number(allocationSumResult.rows[0].allocated);
      if (allocated + Number(amount_usd) > Number(budget.total_amount_usd)) {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Allocation exceeds budget total' });
      }

      const insertResult = await client.query(
        `INSERT INTO treasury_allocations
         (budget_id, allocation_name, amount_usd, emergency_flag, created_by)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [id, allocation_name, amount_usd, emergency_flag, req.guardian.id],
      );
      const allocation = insertResult.rows[0];
      await createEOAGAuditEvent(client, {
        hookId: 'governance-decision-hook',
        entityType: 'treasury_allocation',
        entityId: allocation.id,
        details: allocation,
        actorId: req.guardian.id,
      });
      await createEvidenceLog(client, {
        entityType: 'treasury_allocation',
        entityId: allocation.id,
        action: 'PROPOSE',
        details: allocation,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.status(201).json({ allocation });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta allocation error', error);
      return res.status(500).json({ error: 'Failed to create allocation' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/allocations/:id/approve',
  authenticateToken,
  requireRole('admin', 'oversight'),
  param('id').isUUID(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;
      const result = await client.query(
        `UPDATE treasury_allocations
         SET status = 'approved', approved_by = $1, approved_at = CURRENT_TIMESTAMP
         WHERE id = $2 AND status = 'proposed'
         RETURNING *`,
        [req.guardian.id, id],
      );
      const allocation = result.rows[0];
      if (!allocation) {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Allocation not found or already approved' });
      }
      await createEOAGAuditEvent(client, {
        hookId: 'governance-decision-hook',
        entityType: 'treasury_allocation',
        entityId: allocation.id,
        status: 'cleared',
        details: { approved_by: req.guardian.id },
        actorId: req.guardian.id,
      });
      await createEvidenceLog(client, {
        entityType: 'treasury_allocation',
        entityId: allocation.id,
        action: 'APPROVE',
        details: allocation,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.json({ allocation });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta allocation approve error', error);
      return res.status(500).json({ error: 'Failed to approve allocation' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/allocations/:id/drawdowns',
  authenticateToken,
  requireRole('executor', 'treasurer'),
  param('id').isUUID(),
  body('account_id').isUUID(),
  body('amount_usd').isFloat({ min: 0.01 }),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;
      const { account_id, amount_usd } = req.body;

      const allocationResult = await client.query('SELECT * FROM treasury_allocations WHERE id = $1', [id]);
      const allocation = allocationResult.rows[0];
      if (!allocation || allocation.status !== 'approved') {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Allocation not approved' });
      }

      const accountResult = await client.query('SELECT * FROM treasury_accounts WHERE id = $1', [account_id]);
      const account = accountResult.rows[0];
      if (!account || !account.active) {
        await client.query('ROLLBACK');
        return res.status(404).json({ error: 'Treasury account not found' });
      }
      if (account.frozen) {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Treasury account frozen' });
      }

      const block = await ensureNoJudicialBlock(client, { scopeType: 'account', scopeId: account_id });
      if (block) {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Judicial enforcement active', block });
      }

      const drawdownSum = await client.query(
        `SELECT COALESCE(SUM(amount_usd), 0) AS total
         FROM treasury_drawdowns
         WHERE allocation_id = $1
         AND status IN ('requested', 'approved', 'executed')`,
        [id],
      );
      const total = Number(drawdownSum.rows[0].total);
      if (total + Number(amount_usd) > Number(allocation.amount_usd)) {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Drawdown exceeds allocation amount' });
      }

      const insertResult = await client.query(
        `INSERT INTO treasury_drawdowns
         (allocation_id, account_id, amount_usd, requested_by)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [id, account_id, amount_usd, req.guardian.id],
      );
      const drawdown = insertResult.rows[0];
      const eoagId = await createEOAGAuditEvent(client, {
        hookId: 'treasury-transaction-hook',
        entityType: 'treasury_drawdown',
        entityId: drawdown.id,
        details: drawdown,
        actorId: req.guardian.id,
      });
      await client.query(
        'UPDATE treasury_drawdowns SET eoag_audit_id = $1 WHERE id = $2',
        [eoagId, drawdown.id],
      );
      await createEvidenceLog(client, {
        entityType: 'treasury_drawdown',
        entityId: drawdown.id,
        action: 'REQUEST',
        details: drawdown,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.status(201).json({ drawdown });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta drawdown error', error);
      return res.status(500).json({ error: 'Failed to request drawdown' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/drawdowns/:id/approve',
  authenticateToken,
  requireRole('admin', 'approver', 'oversight'),
  param('id').isUUID(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;
      const drawdownResult = await client.query('SELECT * FROM treasury_drawdowns WHERE id = $1 FOR UPDATE', [id]);
      const drawdown = drawdownResult.rows[0];
      if (!drawdown || drawdown.status !== 'requested') {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Drawdown not in requested status' });
      }

      const signature = signPayload({ drawdown_id: id, approver_id: req.guardian.id, ts: new Date().toISOString() });
      await client.query(
        `INSERT INTO treasury_drawdown_approvals (drawdown_id, guardian_id, signature)
         VALUES ($1, $2, $3)
         ON CONFLICT (drawdown_id, guardian_id) DO NOTHING`,
        [id, req.guardian.id, signature],
      );

      const approvalCountResult = await client.query(
        'SELECT COUNT(*)::int AS count FROM treasury_drawdown_approvals WHERE drawdown_id = $1',
        [id],
      );
      const approvalCount = approvalCountResult.rows[0].count;

      const rules = await client.query(
        `SELECT rule_value FROM governance_rules
         WHERE rule_name LIKE 'min_signatures%' AND active = true
         ORDER BY (rule_value->>'threshold_usd')::decimal DESC`,
      );
      let required = 1;
      for (const row of rules.rows) {
        const threshold = Number(row.rule_value?.threshold_usd || 0);
        if (Number(drawdown.amount_usd) >= threshold) {
          required = Number(row.rule_value?.min_signatures || required);
          break;
        }
      }

      if (approvalCount >= required) {
        await client.query(
          `UPDATE treasury_drawdowns
           SET status = 'approved', approved_by = $1, approved_at = CURRENT_TIMESTAMP
           WHERE id = $2`,
          [req.guardian.id, id],
        );
      }

      await createEvidenceLog(client, {
        entityType: 'treasury_drawdown',
        entityId: drawdown.id,
        action: 'APPROVE',
        details: { approvalCount, required },
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.json({ status: approvalCount >= required ? 'approved' : 'requested', approvals: { count: approvalCount, required } });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta drawdown approve error', error);
      return res.status(500).json({ error: 'Failed to approve drawdown' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/drawdowns/:id/execute',
  authenticateToken,
  requireRole('executor', 'treasurer'),
  param('id').isUUID(),
  body('dbis_settlement_id').trim().notEmpty(),
  body('efctia_reference').trim().notEmpty(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;
      const { dbis_settlement_id, efctia_reference } = req.body;

      const drawdownResult = await client.query('SELECT * FROM treasury_drawdowns WHERE id = $1 FOR UPDATE', [id]);
      const drawdown = drawdownResult.rows[0];
      if (!drawdown || drawdown.status !== 'approved') {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Drawdown not approved for execution' });
      }

      const judicialBlock = await ensureNoJudicialBlock(client, { scopeType: 'drawdown', scopeId: id });
      if (judicialBlock) {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Judicial enforcement active', block: judicialBlock });
      }

      const accountResult = await client.query('SELECT * FROM treasury_accounts WHERE id = $1 FOR UPDATE', [drawdown.account_id]);
      const account = accountResult.rows[0];
      if (!account || account.frozen) {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'Treasury account unavailable' });
      }

      const reserveCheck = await enforceReserveRatio(client, { deltaUsd: -Number(drawdown.amount_usd) });
      if (!reserveCheck.ok) {
        await client.query('ROLLBACK');
        return res.status(403).json({
          error: 'Reserve ratio breach',
          ratio: reserveCheck.ratio,
          minimum: reserveCheck.minRatio,
        });
      }

      const eoagResult = await client.query(
        `SELECT status FROM eoag_audit_events WHERE id = $1`,
        [drawdown.eoag_audit_id],
      );
      if (!eoagResult.rows.length || eoagResult.rows[0].status !== 'cleared') {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: 'EOAG clearance required before execution' });
      }

      const newBalance = Number(account.balance_usd) - Number(drawdown.amount_usd);
      if (newBalance < 0) {
        await client.query('ROLLBACK');
        return res.status(400).json({ error: 'Insufficient treasury balance' });
      }

      await client.query(
        `UPDATE treasury_accounts SET balance_usd = $1 WHERE id = $2`,
        [newBalance, account.id],
      );

      const txResult = await client.query(
        `INSERT INTO treasury_transactions
         (account_id, transaction_type, amount_usd, balance_after, description, external_reference, dbis_settlement_id, efctia_reference, eoag_audit_id, created_by)
         VALUES ($1, 'withdrawal', $2, $3, $4, $5, $6, $7, $8, $9)
         RETURNING *`,
        [
          account.id,
          drawdown.amount_usd,
          newBalance,
          'ETA drawdown execution',
          drawdown.id,
          dbis_settlement_id,
          efctia_reference,
          drawdown.eoag_audit_id,
          req.guardian.id,
        ],
      );

      await client.query(
        `UPDATE treasury_drawdowns
         SET status = 'executed', executed_by = $1, executed_at = CURRENT_TIMESTAMP,
             dbis_settlement_id = $2, efctia_reference = $3
         WHERE id = $4`,
        [req.guardian.id, dbis_settlement_id, efctia_reference, drawdown.id],
      );

      await createEvidenceLog(client, {
        entityType: 'treasury_drawdown',
        entityId: drawdown.id,
        action: 'EXECUTE',
        details: { transaction_id: txResult.rows[0].id, dbis_settlement_id, efctia_reference },
        actorId: req.guardian.id,
      });
      await createEOAGAuditEvent(client, {
        hookId: 'treasury-settlement-hook',
        entityType: 'treasury_transaction',
        entityId: txResult.rows[0].id,
        status: 'cleared',
        details: txResult.rows[0],
        actorId: req.guardian.id,
      });

      await client.query('COMMIT');
      return res.json({ transaction: txResult.rows[0], balance_after: newBalance });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] eta drawdown execute error', error);
      return res.status(500).json({ error: 'Failed to execute drawdown' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/eoag/:id/clear',
  authenticateToken,
  requireRole('auditor', 'oversight', 'admin'),
  param('id').isUUID(),
  body('status').optional().isIn(['cleared', 'blocked']),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      const { id } = req.params;
      const { status = 'cleared' } = req.body;
      const result = await client.query(
        `UPDATE eoag_audit_events SET status = $1 WHERE id = $2 RETURNING *`,
        [status, id],
      );
      const audit = result.rows[0];
      if (!audit) {
        return res.status(404).json({ error: 'EOAG audit event not found' });
      }
      return res.json({ audit });
    } catch (error) {
      console.error('[relief-system] eoag clear error', error);
      return res.status(500).json({ error: 'Failed to update EOAG audit event' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/judicial/actions',
  authenticateToken,
  requireRole('admin', 'oversight', 'auditor'),
  body('action_type').isIn(['freeze', 'reverse', 'sanction']),
  body('scope_type').isIn(['account', 'budget', 'allocation', 'drawdown', 'global']),
  body('scope_id').optional().isUUID(),
  body('reason').trim().isLength({ min: 5, max: 1000 }),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { action_type, scope_type, scope_id, reason } = req.body;
      const insertResult = await client.query(
        `INSERT INTO judicial_actions
         (action_type, scope_type, scope_id, reason, issued_by)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [action_type, scope_type, scope_id || null, reason, req.guardian.id],
      );
      const action = insertResult.rows[0];

      if (action_type === 'freeze' && scope_type === 'account' && scope_id) {
        await client.query(
          `UPDATE treasury_accounts SET frozen = true WHERE id = $1`,
          [scope_id],
        );
      }

      await createEvidenceLog(client, {
        entityType: 'judicial_action',
        entityId: action.id,
        action: 'ISSUE',
        details: action,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.status(201).json({ action });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] judicial action error', error);
      return res.status(500).json({ error: 'Failed to record judicial action' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/judicial/actions/:id/lift',
  authenticateToken,
  requireRole('admin', 'oversight', 'auditor'),
  param('id').isUUID(),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const { id } = req.params;
      const result = await client.query(
        `UPDATE judicial_actions SET status = 'lifted' WHERE id = $1 RETURNING *`,
        [id],
      );
      const action = result.rows[0];
      if (!action) {
        await client.query('ROLLBACK');
        return res.status(404).json({ error: 'Judicial action not found' });
      }
      if (action.action_type === 'freeze' && action.scope_type === 'account' && action.scope_id) {
        await client.query(
          `UPDATE treasury_accounts SET frozen = false WHERE id = $1`,
          [action.scope_id],
        );
      }
      await createEvidenceLog(client, {
        entityType: 'judicial_action',
        entityId: action.id,
        action: 'LIFT',
        details: action,
        actorId: req.guardian.id,
      });
      await client.query('COMMIT');
      return res.json({ action });
    } catch (error) {
      await client.query('ROLLBACK');
      console.error('[relief-system] judicial lift error', error);
      return res.status(500).json({ error: 'Failed to lift judicial action' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/emergency/activate',
  authenticateToken,
  requireRole('admin', 'oversight'),
  body('reason').trim().isLength({ min: 5, max: 500 }),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      const { reason } = req.body;
      const result = await client.query(
        `INSERT INTO treasury_emergency_controls (status, reason, activated_by)
         VALUES ('active', $1, $2)
         RETURNING *`,
        [reason, req.guardian.id],
      );
      return res.status(201).json({ emergency: result.rows[0] });
    } catch (error) {
      console.error('[relief-system] emergency activate error', error);
      return res.status(500).json({ error: 'Failed to activate emergency controls' });
    } finally {
      client.release();
    }
  },
);

app.post(
  '/api/eta/emergency/deactivate',
  authenticateToken,
  requireRole('admin', 'oversight'),
  body('reason').trim().isLength({ min: 5, max: 500 }),
  validateRequest,
  async (req, res) => {
    const client = await pool.connect();
    try {
      const { reason } = req.body;
      const result = await client.query(
        `UPDATE treasury_emergency_controls
         SET status = 'inactive', deactivated_at = CURRENT_TIMESTAMP, reason = $1
         WHERE status = 'active'
         RETURNING *`,
        [reason],
      );
      return res.json({ emergency: result.rows });
    } catch (error) {
      console.error('[relief-system] emergency deactivate error', error);
      return res.status(500).json({ error: 'Failed to deactivate emergency controls' });
    } finally {
      client.release();
    }
  },
);

app.get('/api/metrics/dashboard', async (_req, res) => {
  try {
    const metricsResult = await pool.query(
      'SELECT * FROM metrics_snapshots ORDER BY snapshot_date DESC LIMIT 30',
    );

    const summaryResult = await pool.query(
      `SELECT
          COUNT(*) FILTER (WHERE status = 'approved') AS approved_count,
          COUNT(*) FILTER (WHERE status = 'disbursed') AS disbursed_count,
          COALESCE(SUM(amount_usd) FILTER (WHERE status IN ('approved', 'disbursed')), 0) AS total_relief,
          COUNT(DISTINCT beneficiary_hint) AS unique_beneficiaries
        FROM relief_events`,
    );

    return res.json({ current: summaryResult.rows[0], history: metricsResult.rows });
  } catch (error) {
    console.error('[relief-system] metrics error', error);
    return res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------
app.get('/api/audit/log', authenticateToken, requireRole('admin', 'auditor'), async (req, res) => {
  try {
    const page = Math.max(Number(req.query.page) || 1, 1);
    const limit = Math.min(Math.max(Number(req.query.limit) || 50, 1), 200);
    const offset = (page - 1) * limit;

    const result = await pool.query(
      `SELECT al.*, g.username AS actor_username
         FROM audit_log al
         LEFT JOIN guardians g ON al.actor_id = g.id
         ORDER BY al.created_at DESC
         LIMIT $1 OFFSET $2`,
      [limit, offset],
    );

    const countResult = await pool.query('SELECT COUNT(*)::int AS count FROM audit_log');
    const total = countResult.rows[0].count;

    return res.json({
      logs: result.rows,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('[relief-system] audit log error', error);
    return res.status(500).json({ error: 'Failed to fetch audit log' });
  }
});

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
app.get('/health', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    return res.json({ status: 'healthy', timestamp: new Date().toISOString(), version: '1.1.0' });
  } catch (error) {
    return res.status(503).json({ status: 'unhealthy', error: 'Database connection failed' });
  }
});

app.use((err, _req, res, _next) => {
  console.error('[relief-system] unhandled error', err);
  res.status(500).json({ error: 'Unexpected server error' });
});

app.listen(PORT, () => {
  console.log(`[relief-system] server listening on port ${PORT}`);
});
