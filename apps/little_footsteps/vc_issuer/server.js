import 'dotenv/config';
import express from 'express';
import crypto from 'crypto';
import fs from 'fs/promises';
import { Pool } from 'pg';
import cors from 'cors';

const app = express();
app.use(express.json({ limit: '1mb' }));

const allowOrigins = process.env.CORS_ALLOW_ORIGINS?.split(',').map((origin) => origin.trim()).filter(Boolean) ?? [];
if (allowOrigins.length > 0) {
  app.use(
    cors({
      origin: allowOrigins,
      credentials: true,
    }),
  );
} else {
  app.use(cors());
}

app.use((req, res, next) => {
  const start = process.hrtime.bigint();
  const requestId = req.headers['x-request-id'] ?? crypto.randomUUID();
  res.setHeader('x-request-id', requestId);
  res.locals.requestId = requestId;

  res.on('finish', () => {
    const durationMs = Number(process.hrtime.bigint() - start) / 1_000_000;
    const logEvent = {
      timestamp: new Date().toISOString(),
      level: 'info',
      event: 'http_request',
      method: req.method,
      path: req.originalUrl,
      status: res.statusCode,
      duration_ms: Number(durationMs.toFixed(2)),
      request_id: requestId,
    };
    console.log(JSON.stringify(logEvent));
  });

  next();
});

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  throw new Error('DATABASE_URL environment variable is required for ledger connectivity');
}

const pool = new Pool({ connectionString: databaseUrl });

async function ensureSchema() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS ledger_events (
        id UUID PRIMARY KEY,
        direction TEXT NOT NULL CHECK (direction IN ('INFLOW', 'OUTFLOW')),
        amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
        currency TEXT NOT NULL,
        purpose TEXT,
        source TEXT,
        occurred_at TIMESTAMPTZ NOT NULL,
        beneficiary TEXT,
        tags TEXT[],
        vc_id TEXT,
        metadata JSONB DEFAULT '{}'::jsonb
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS issued_credentials (
        id UUID PRIMARY KEY,
        type TEXT NOT NULL,
        subject JSONB NOT NULL,
        vc JSONB NOT NULL,
        issued_at TIMESTAMPTZ NOT NULL,
        ledger_event_id UUID REFERENCES ledger_events(id) ON DELETE SET NULL
      );
    `);
  } finally {
    client.release();
  }
}

await ensureSchema();

const issuerDid = process.env.VC_ISSUER_DID;
if (!issuerDid) {
  throw new Error('VC_ISSUER_DID must be configured to sign verifiable credentials');
}

const privateKeyPath = process.env.VC_PRIVATE_KEY_PATH ?? 'state/little_footsteps/keys/issuer-ed25519-private.key';
let signingKey;

async function loadPrivateKey() {
  if (signingKey) {
    return signingKey;
  }
  const pem = await fs.readFile(privateKeyPath, 'utf8');
  signingKey = crypto.createPrivateKey({
    key: pem,
    format: 'pem',
    type: 'pkcs8',
  });
  return signingKey;
}

const trustRegistryPath = process.env.TRUST_REGISTRY_PATH ?? 'docs/little_footsteps/trust_registry.json';
let trustRegistry;

async function loadTrustRegistry() {
  if (trustRegistry) {
    return trustRegistry;
  }
  try {
    const contents = await fs.readFile(trustRegistryPath, 'utf8');
    trustRegistry = JSON.parse(contents);
  } catch (error) {
    console.warn('Unable to load trust registry; defaulting to empty list', error);
    trustRegistry = { recognizedCredentials: [] };
  }
  return trustRegistry;
}

function encodeBase64Url(value) {
  return Buffer.from(JSON.stringify(value)).toString('base64url');
}

async function signCredential(payload) {
  const key = await loadPrivateKey();
  const protectedHeader = {
    alg: 'EdDSA',
    typ: 'JWT',
    kid: `${issuerDid}#ed25519-2024`,
  };

  const headerB64 = encodeBase64Url(protectedHeader);
  const payloadB64 = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const data = `${headerB64}.${payloadB64}`;
  const signature = crypto.sign(null, Buffer.from(data), key).toString('base64url');
  return `${data}.${signature}`;
}

function buildCredential(type, subject) {
  return {
    '@context': ['https://www.w3.org/ns/credentials/v2', 'https://schema.org'],
    type: ['VerifiableCredential', type],
    issuer: issuerDid,
    issuanceDate: new Date().toISOString(),
    credentialSubject: subject,
  };
}

async function recordLedgerEvent(event) {
  const client = await pool.connect();
  try {
    const id = crypto.randomUUID();
    const occurredAt = event.occurred_at ?? new Date().toISOString();
    await client.query(
      `INSERT INTO ledger_events (
        id, direction, amount_cents, currency, purpose, source, occurred_at, beneficiary, tags, vc_id, metadata
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
      )`,
      [
        id,
        event.direction,
        event.amount_cents,
        event.currency,
        event.purpose ?? null,
        event.source ?? null,
        occurredAt,
        event.beneficiary ?? null,
        event.tags ?? null,
        event.vc_id ?? null,
        event.metadata ?? {},
      ],
    );
    return { ...event, id, occurred_at: occurredAt };
  } finally {
    client.release();
  }
}

async function storeCredential(record) {
  const client = await pool.connect();
  try {
    await client.query(
      `INSERT INTO issued_credentials (id, type, subject, vc, issued_at, ledger_event_id)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [
        record.id,
        record.type,
        record.subject,
        record.vc,
        record.issued_at,
        record.ledger_event_id ?? null,
      ],
    );
  } finally {
    client.release();
  }
}

app.get('/healthz', (_req, res) => {
  res.json({ status: 'ok', issuer: issuerDid });
});

app.post('/ledger/events', async (req, res, next) => {
  try {
    const { direction, amount_cents, currency } = req.body;
    if (!direction || !amount_cents || !currency) {
      return res.status(400).json({ error: 'direction, amount_cents, and currency are required' });
    }
    const saved = await recordLedgerEvent({
      direction,
      amount_cents,
      currency,
      purpose: req.body.purpose,
      source: req.body.source,
      occurred_at: req.body.occurred_at,
      beneficiary: req.body.beneficiary,
      tags: req.body.tags,
      vc_id: req.body.vc_id,
      metadata: req.body.metadata,
    });
    res.status(201).json(saved);
  } catch (error) {
    next(error);
  }
});

app.get('/ledger/events', async (req, res, next) => {
  try {
    const limit = Number.parseInt(req.query.limit ?? '50', 10);
    const client = await pool.connect();
    try {
      const { rows } = await client.query(
        `SELECT * FROM ledger_events ORDER BY occurred_at DESC LIMIT $1`,
        [Number.isNaN(limit) ? 50 : limit],
      );
      res.json(rows);
    } finally {
      client.release();
    }
  } catch (error) {
    next(error);
  }
});

app.get('/metrics/totals', async (_req, res, next) => {
  try {
    const client = await pool.connect();
    try {
      const { rows } = await client.query(
        `SELECT
            COALESCE(SUM(CASE WHEN direction = 'INFLOW' THEN amount_cents END), 0) AS inflows,
            COALESCE(SUM(CASE WHEN direction = 'OUTFLOW' THEN amount_cents END), 0) AS outflows
         FROM ledger_events
         WHERE occurred_at::date = CURRENT_DATE`
      );
      const inflows = Number(rows[0].inflows ?? 0);
      const outflows = Number(rows[0].outflows ?? 0);
      res.json({ inflows, outflows, net: inflows - outflows });
    } finally {
      client.release();
    }
  } catch (error) {
    next(error);
  }
});

app.post('/issue/childcare-voucher', async (req, res, next) => {
  try {
    const registry = await loadTrustRegistry();
    const credentialSlug = 'LittleFootstepsChildcareVoucher';
    if (!registry.recognizedCredentials?.includes(credentialSlug)) {
      return res.status(409).json({
        error: 'credential_not_recognized',
        message: `${credentialSlug} is not present in trust registry`,
      });
    }

    const { credentialSubject, ledgerEvent } = req.body;
    if (!credentialSubject) {
      return res.status(400).json({ error: 'credentialSubject is required' });
    }

    const credential = buildCredential(credentialSlug, credentialSubject);
    const jws = await signCredential(credential);
    const vcId = `vc:childcare:${crypto.randomUUID()}`;

    let savedLedgerEvent = null;
    if (ledgerEvent) {
      savedLedgerEvent = await recordLedgerEvent({
        ...ledgerEvent,
        vc_id: vcId,
      });
    }

    const credentialRecord = {
      id: crypto.randomUUID(),
      type: credentialSlug,
      subject: credentialSubject,
      vc: { credential, proof: { type: 'Ed25519Signature2020', created: new Date().toISOString(), jws } },
      issued_at: new Date().toISOString(),
      ledger_event_id: savedLedgerEvent?.id,
    };

    await storeCredential(credentialRecord);

    res.status(201).json({
      vcId,
      credential,
      proof: credentialRecord.vc.proof,
      ledgerEvent: savedLedgerEvent,
    });
  } catch (error) {
    next(error);
  }
});

app.use((err, _req, res, _next) => {
  console.error(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'error',
      event: 'issuer_error',
      message: err.message,
      stack: err.stack,
    }),
  );
  res.status(500).json({ error: 'internal_error', message: err.message });
});

const port = Number.parseInt(process.env.PORT ?? '4000', 10);
app.listen(port, () => {
  console.log(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'info',
      event: 'issuer_started',
      port,
      issuer: issuerDid,
    }),
  );
});
