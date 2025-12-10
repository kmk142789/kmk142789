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
      `SELECT account_type, COUNT(*) AS account_count, SUM(balance_usd) AS total_balance
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
