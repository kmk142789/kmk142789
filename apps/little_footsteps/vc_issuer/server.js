import 'dotenv/config';
import express from 'express';
import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'node:path';
import { Pool } from 'pg';
import cors from 'cors';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

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

const receiptsLogPath =
  process.env.DONATION_RECEIPTS_LOG_PATH ?? 'state/little_footsteps/donation_receipts.jsonl';
const telemetryLogPath =
  process.env.DONATION_TELEMETRY_LOG_PATH ?? 'state/little_footsteps/dashboard/donations.jsonl';
const credentialStatusLogPath =
  process.env.CREDENTIAL_STATUS_LOG_PATH ?? 'state/little_footsteps/credential_status.jsonl';
const amendmentsPath = process.env.AMENDMENTS_PATH ?? 'data/governance/amendments.json';
const ledgerProofsPath = process.env.AUDIT_LEDGER_PATH ?? 'ledger/little_footsteps_bank.jsonl';
const proofsDir = process.env.AUDIT_PROOFS_DIR ?? 'proofs/little_footsteps_bank';
const continuityPath = process.env.CONTINUITY_CHECKPOINTS_PATH ?? 'state/continuity/multisig_recovery.jsonl';

const streamClients = new Set();
const STREAM_HEARTBEAT_MS = 15000;

async function ensureSchema() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS ledger_events (
        id UUID PRIMARY KEY,
        direction TEXT NOT NULL CHECK (direction IN ('INFLOW', 'OUTFLOW')),
        amount_cents BIGINT NOT NULL CHECK (amount_cents >= 0),
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
        ledger_event_id UUID REFERENCES ledger_events(id) ON DELETE SET NULL,
        revoked_at TIMESTAMPTZ,
        revocation_reason TEXT,
        revoked_by TEXT
      );
    `);

    try {
      await client.query(
        `ALTER TABLE ledger_events ALTER COLUMN amount_cents TYPE BIGINT USING amount_cents::bigint`,
      );
    } catch (error) {
      if (error.code !== '42804' && error.code !== '42704' && error.code !== '0A000') {
        // Ignore conversion failures when the table is empty or already migrated; rethrow others.
        throw error;
      }
    }

    try {
      await client.query(
        `ALTER TABLE issued_credentials
           ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ,
           ADD COLUMN IF NOT EXISTS revocation_reason TEXT,
           ADD COLUMN IF NOT EXISTS revoked_by TEXT`,
      );
    } catch (error) {
      if (error.code !== '42P07' && error.code !== '42701') {
        throw error;
      }
    }
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
let signingKeyMtimeMs;

function normaliseLedgerEntry(entry) {
  return {
    ...entry,
    amount_cents: Number.parseInt(entry.amount_cents, 10),
  };
}

async function fetchDailyTotals() {
  const client = await pool.connect();
  try {
    const { rows } = await client.query(
      `SELECT
          COALESCE(SUM(CASE WHEN direction = 'INFLOW' THEN amount_cents END), 0) AS inflows,
          COALESCE(SUM(CASE WHEN direction = 'OUTFLOW' THEN amount_cents END), 0) AS outflows
       FROM ledger_events
       WHERE occurred_at::date = CURRENT_DATE`,
    );

    const inflows = BigInt(rows[0].inflows ?? 0);
    const outflows = BigInt(rows[0].outflows ?? 0);

    return {
      inflows: Number(inflows),
      outflows: Number(outflows),
      net: Number(inflows - outflows),
    };
  } finally {
    client.release();
  }
}

function writeStream(res, payload) {
  res.write(`event: ledger\n`);
  res.write(`data: ${JSON.stringify(payload)}\n\n`);
}

async function broadcastLedgerUpdate(entry) {
  if (streamClients.size === 0) {
    return;
  }

  try {
    const totals = await fetchDailyTotals();
    const payload = { entry: normaliseLedgerEntry(entry), totals };
    for (const res of streamClients) {
      writeStream(res, payload);
    }
  } catch (error) {
    console.warn('Unable to broadcast ledger update', error);
  }
}

setInterval(() => {
  for (const res of streamClients) {
    res.write(`event: heartbeat\ndata: {}\n\n`);
  }
}, STREAM_HEARTBEAT_MS);

async function loadPrivateKey() {
  const stats = await fs.stat(privateKeyPath);
  if (signingKey && signingKeyMtimeMs === stats.mtimeMs) {
    return signingKey;
  }
  const pem = await fs.readFile(privateKeyPath, 'utf8');
  signingKey = crypto.createPrivateKey({
    key: pem,
    format: 'pem',
    type: 'pkcs8',
  });
  signingKeyMtimeMs = stats.mtimeMs;
  return signingKey;
}

const trustRegistryPath = process.env.TRUST_REGISTRY_PATH ?? 'docs/little_footsteps/trust_registry.json';
let trustRegistry;
let trustRegistryMtimeMs;

async function loadTrustRegistry() {
  try {
    const stats = await fs.stat(trustRegistryPath);
    if (trustRegistry && trustRegistryMtimeMs === stats.mtimeMs) {
      return trustRegistry;
    }
    const contents = await fs.readFile(trustRegistryPath, 'utf8');
    trustRegistry = JSON.parse(contents);
    trustRegistryMtimeMs = stats.mtimeMs;
    if (trustRegistry.issuer && trustRegistry.issuer !== issuerDid) {
      throw new Error(
        `Trust registry issuer ${trustRegistry.issuer} does not match configured VC_ISSUER_DID ${issuerDid}`,
      );
    }
    if (!Array.isArray(trustRegistry.recognizedCredentials)) {
      trustRegistry.recognizedCredentials = [];
    }
  } catch (error) {
    console.warn('Unable to load trust registry; defaulting to empty list', error);
    trustRegistry = { recognizedCredentials: [] };
  }
  return trustRegistry;
}

async function loadAmendments() {
  try {
    const contents = await fs.readFile(amendmentsPath, 'utf8');
    const parsed = JSON.parse(contents);
    return parsed.amendments ?? [];
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.warn('Unable to load amendments file', error);
    }
    return [];
  }
}

function normaliseProofEntry(entry) {
  const seqValue = entry.seq ?? entry.sequence;
  const seq = Number.isFinite(Number(seqValue)) ? Number(seqValue) : null;
  const proofPath =
    seq === null
      ? null
      : path.posix.join(proofsDir, `entry_${String(seq).padStart(5, '0')}.json`);

  return {
    seq,
    digest: entry.digest ?? entry.compliance?.transaction_digest ?? null,
    direction: entry.direction ?? null,
    amount: entry.amount ?? null,
    asset: entry.asset ?? entry.currency ?? null,
    timestamp: entry.timestamp ?? null,
    proof_path: proofPath,
    ots_receipt: entry.ots_receipt ?? entry.compliance?.ots_receipt ?? null,
  };
}

async function loadLedgerProofs() {
  try {
    const contents = await fs.readFile(ledgerProofsPath, 'utf8');
    return contents
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => normaliseProofEntry(JSON.parse(line)));
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.warn('Unable to load ledger proofs', error);
    }
    return [];
  }
}

function normaliseContinuityCheckpoint(entry) {
  return {
    seq: entry.seq ?? entry.sequence ?? null,
    digest: entry.digest ?? entry.checksum ?? null,
    timestamp: entry.timestamp ?? entry.published_at ?? null,
    threshold: entry.threshold ?? entry.quorum ?? 0,
    trustees: entry.trustees ?? entry.signers ?? [],
  };
}

async function loadContinuityCheckpoints() {
  try {
    const contents = await fs.readFile(continuityPath, 'utf8');
    return contents
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => normaliseContinuityCheckpoint(JSON.parse(line)));
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.warn('Unable to load continuity checkpoints', error);
    }
    return [];
  }
}

async function buildAuditTrail(limit = 20) {
  const ledger = await loadLedgerProofs();
  const continuity = await loadContinuityCheckpoints();
  return {
    ledger: ledger.slice(-limit).reverse(),
    continuity: continuity.slice(-limit).reverse(),
  };
}

const credentialSchemaDir = process.env.CREDENTIAL_SCHEMA_DIR ?? 'docs/little_footsteps/credentials/schemas';
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
let credentialSchemas;
let credentialSchemasMtimeMs;

async function getCredentialSchemasMtime() {
  const files = await fs.readdir(credentialSchemaDir);
  const jsonFiles = files.filter((file) => file.endsWith('.json'));
  const stats = await Promise.all(
    jsonFiles.map((file) => fs.stat(path.join(credentialSchemaDir, file))),
  );
  return stats.reduce((latest, stat) => Math.max(latest, stat.mtimeMs), 0);
}

async function loadCredentialSchemas() {
  try {
    const latestMtime = await getCredentialSchemasMtime();
    if (credentialSchemas && credentialSchemasMtimeMs === latestMtime) {
      return credentialSchemas;
    }
    credentialSchemasMtimeMs = latestMtime;
    credentialSchemas = new Map();
    const files = await fs.readdir(credentialSchemaDir);
    for (const file of files) {
      if (!file.endsWith('.json')) continue;
      const raw = await fs.readFile(path.join(credentialSchemaDir, file), 'utf8');
      const schema = JSON.parse(raw);
      const slug = schema.title ?? path.basename(file, '.json');
      credentialSchemas.set(slug, { schema, validate: ajv.compile(schema) });
    }
  } catch (error) {
    console.warn('Unable to load credential schemas', error);
    if (!credentialSchemas) {
      credentialSchemas = new Map();
    }
  }

  return credentialSchemas;
}

async function validateCredentialSubject(slug, subject) {
  const schemas = await loadCredentialSchemas();
  const schemaRecord = schemas.get(slug);
  if (!schemaRecord) {
    return { valid: true };
  }

  const valid = schemaRecord.validate(subject);
  return {
    valid,
    errors: schemaRecord.validate.errors?.map((err) => ({ instancePath: err.instancePath, message: err.message })) ?? [],
  };
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
    const amountMinor = BigInt(String(event.amount_cents));
    await client.query(
      `INSERT INTO ledger_events (
        id, direction, amount_cents, currency, purpose, source, occurred_at, beneficiary, tags, vc_id, metadata
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
      )`,
      [
        id,
        event.direction,
        amountMinor.toString(),
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
    const savedEvent = { ...event, amount_cents: amountMinor.toString(), id, occurred_at: occurredAt };
    broadcastLedgerUpdate(savedEvent).catch((error) => {
      console.warn('Unable to dispatch ledger stream event', error);
    });
    return savedEvent;
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

async function recordCredentialStatus({ id, type, issued_at, ledger_event_id, status, reason, actor }) {
  const payload = {
    timestamp: new Date().toISOString(),
    credential_id: id,
    credential_type: type,
    issued_at,
    ledger_event_id: ledger_event_id ?? null,
    status,
    reason: reason ?? null,
    actor: actor ?? 'issuer',
  };
  await appendJsonl(credentialStatusLogPath, payload);
  return payload;
}

function normaliseStatusRow(row) {
  const toIso = (value) => (value instanceof Date ? value.toISOString() : value ?? null);

  return {
    id: row.id,
    type: row.type,
    issued_at: toIso(row.issued_at),
    ledger_event_id: row.ledger_event_id ?? null,
    revoked: Boolean(row.revoked_at),
    revoked_at: toIso(row.revoked_at),
    revocation_reason: row.revocation_reason ?? null,
    revoked_by: row.revoked_by ?? null,
  };
}

async function fetchCredentialStatus(id) {
  const client = await pool.connect();
  try {
    const { rows } = await client.query(
      `SELECT id, type, issued_at, ledger_event_id, revoked_at, revocation_reason, revoked_by
         FROM issued_credentials
        WHERE id = $1`,
      [id],
    );

    if (!rows.length) {
      return null;
    }

    return normaliseStatusRow(rows[0]);
  } finally {
    client.release();
  }
}

async function revokeCredential({ id, reason, actor }) {
  const client = await pool.connect();
  try {
    const { rows: existing } = await client.query(
      `SELECT id, revoked_at, revocation_reason, revoked_by FROM issued_credentials WHERE id = $1`,
      [id],
    );

    if (!existing.length) {
      return null;
    }

    const revokedAt = existing[0].revoked_at ?? new Date().toISOString();

    const { rows } = await client.query(
      `UPDATE issued_credentials
          SET revoked_at = COALESCE(revoked_at, $2::timestamptz),
              revocation_reason = COALESCE($3, revocation_reason),
              revoked_by = COALESCE($4, revoked_by)
        WHERE id = $1
      RETURNING id, type, issued_at, ledger_event_id, revoked_at, revocation_reason, revoked_by`,
      [id, revokedAt, reason ?? null, actor ?? null],
    );

    const status = normaliseStatusRow(rows[0]);
    await recordCredentialStatus({
      id,
      type: status.type,
      issued_at: status.issued_at,
      ledger_event_id: status.ledger_event_id,
      status: 'revoked',
      reason: status.revocation_reason ?? reason ?? 'revoked',
      actor: status.revoked_by ?? actor ?? 'issuer',
    });

    return status;
  } finally {
    client.release();
  }
}

function minorUnitDecimals(currency) {
  switch (currency) {
    case 'USD':
    case 'CAD':
    case 'EUR':
    case 'GBP':
      return 2;
    case 'BTC':
      return 8;
    case 'ETH':
      return 18;
    default:
      return 2;
  }
}

function decimalToMinorUnits(amount, decimals) {
  const [whole, fraction = ''] = amount.split('.');
  if (!/^\d+$/.test(whole)) {
    throw new Error('amount must be a positive number');
  }
  if (fraction.length > decimals) {
    throw new Error(`amount supports at most ${decimals} decimal places`);
  }
  const paddedFraction = fraction.padEnd(decimals, '0');
  const scale = 10n ** BigInt(decimals);
  const wholeUnits = BigInt(whole) * scale;
  const fractionUnits = paddedFraction ? BigInt(paddedFraction) : 0n;
  return wholeUnits + fractionUnits;
}

function parseMinorUnits(body, currency) {
  if (body.amount_minor !== undefined && body.amount_minor !== null) {
    const minor = BigInt(String(body.amount_minor));
    if (minor <= 0n) {
      throw new Error('amount_minor must be greater than zero');
    }
    return minor;
  }

  if (body.amount === undefined || body.amount === null) {
    throw new Error('amount is required');
  }

  const amountStr = typeof body.amount === 'number' ? body.amount.toString() : String(body.amount);
  if (amountStr.toLowerCase().includes('e')) {
    throw new Error('amount must be provided as a decimal string');
  }
  if (!/^\d+(\.\d+)?$/.test(amountStr)) {
    throw new Error('amount must be a positive number');
  }

  const decimals = minorUnitDecimals(currency);
  const minor = decimalToMinorUnits(amountStr, decimals);
  if (minor <= 0n) {
    throw new Error('amount must be greater than zero');
  }
  return minor;
}

function formatMajorAmount(minorUnits, currency) {
  const decimals = minorUnitDecimals(currency);
  const negative = minorUnits < 0n;
  const absolute = negative ? -minorUnits : minorUnits;
  const scale = 10n ** BigInt(decimals);
  const whole = absolute / scale;
  const fraction = absolute % scale;
  const fractionStr = fraction.toString().padStart(decimals, '0');
  const combined = decimals === 0 ? whole.toString() : `${whole.toString()}.${fractionStr}`;
  const trimmed =
    decimals === 0 ? combined : combined.replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
  let withLeadingZero = trimmed;
  if (trimmed.startsWith('.')) {
    withLeadingZero = `0${trimmed}`;
  } else if (trimmed.startsWith('-.')) {
    withLeadingZero = `-0${trimmed.slice(1)}`;
  }
  const normalised = withLeadingZero === '' ? '0' : withLeadingZero;
  return negative ? `-${normalised}` : normalised;
}

function normalizePaymentMethod(method) {
  const normalized = String(method ?? '').trim().toLowerCase();
  const map = {
    btc: 'BTC',
    bitcoin: 'BTC',
    eth: 'ETH',
    ethereum: 'ETH',
    stripe: 'STRIPE',
    paypal: 'PAYPAL',
  };
  const value = map[normalized];
  if (!value) {
    throw new Error('Unsupported payment method');
  }
  return value;
}

function parseLedgerAmount(value) {
  const amount = BigInt(String(value));
  if (amount < 0n) {
    throw new Error('amount_cents must be zero or greater');
  }
  return amount;
}

function validateLedgerDirection(direction) {
  const normalized = String(direction ?? '').toUpperCase();
  if (!['INFLOW', 'OUTFLOW'].includes(normalized)) {
    throw new Error('direction must be INFLOW or OUTFLOW');
  }
  return normalized;
}

async function appendJsonl(logPath, payload) {
  const resolved = path.resolve(logPath);
  await fs.mkdir(path.dirname(resolved), { recursive: true });
  await fs.appendFile(resolved, `${JSON.stringify(payload)}\n`, { encoding: 'utf8' });
}

app.get('/healthz', (_req, res) => {
  res.json({ status: 'ok', issuer: issuerDid });
});

app.get('/trust/registry', async (_req, res, next) => {
  try {
    const registry = await loadTrustRegistry();
    res.json({ issuer: issuerDid, registry });
  } catch (error) {
    next(error);
  }
});

app.get('/credentials/:id/status', async (req, res, next) => {
  try {
    const status = await fetchCredentialStatus(req.params.id);
    if (!status) {
      return res.status(404).json({ error: 'credential_not_found' });
    }
    res.json(status);
  } catch (error) {
    next(error);
  }
});

app.post('/credentials/:id/revoke', async (req, res, next) => {
  try {
    const reason = req.body.reason ? String(req.body.reason).trim() : null;
    const actor = req.body.actor ? String(req.body.actor).trim() : null;
    const status = await revokeCredential({ id: req.params.id, reason, actor });

    if (!status) {
      return res.status(404).json({ error: 'credential_not_found' });
    }

    res.json(status);
  } catch (error) {
    next(error);
  }
});

app.post('/donations/intake', async (req, res, next) => {
  try {
    const registry = await loadTrustRegistry();
    const credentialSlug = 'DonationReceiptCredential';
    if (!registry.recognizedCredentials?.includes(credentialSlug)) {
      return res.status(409).json({
        error: 'credential_not_recognized',
        message: `${credentialSlug} is not present in trust registry`,
      });
    }

    const currency = String(req.body.currency ?? '').toUpperCase();
    if (!currency) {
      return res.status(400).json({ error: 'currency is required' });
    }

    let minorUnits;
    try {
      minorUnits = parseMinorUnits(req.body, currency);
    } catch (error) {
      return res.status(400).json({ error: error.message });
    }

    let paymentMethod;
    try {
      paymentMethod = normalizePaymentMethod(req.body.method);
    } catch (error) {
      return res.status(400).json({ error: error.message });
    }

    let occurredAt;
    try {
      const occurredAtDate = req.body.occurred_at ? new Date(req.body.occurred_at) : new Date();
      if (Number.isNaN(occurredAtDate.getTime())) {
        throw new Error('invalid');
      }
      occurredAt = occurredAtDate.toISOString();
    } catch (error) {
      return res.status(400).json({ error: 'occurred_at must be a valid ISO-8601 timestamp' });
    }
    const vcId = `vc:donation:${crypto.randomUUID()}`;
    const reference = req.body.reference ?? vcId;
    const decimals = minorUnitDecimals(currency);
    const majorAmount = formatMajorAmount(minorUnits, currency);

    const ledgerEvent = await recordLedgerEvent({
      direction: 'INFLOW',
      amount_cents: minorUnits.toString(),
      currency,
      purpose: req.body.purpose ?? 'Little Footsteps donation',
      source: req.body.source ?? `donation:${paymentMethod.toLowerCase()}`,
      occurred_at: occurredAt,
      beneficiary: req.body.beneficiary,
      tags: Array.isArray(req.body.tags)
        ? ['donation', paymentMethod.toLowerCase(), ...req.body.tags]
        : ['donation', paymentMethod.toLowerCase()],
      vc_id: vcId,
      metadata: {
        ...(req.body.metadata ?? {}),
        payment_method: paymentMethod,
        transaction: req.body.transaction ?? null,
        reference,
        minor_unit_decimals: decimals,
      },
    });

    const credentialSubject = {
      donation: {
        ledgerEventId: ledgerEvent.id,
        amount: {
          currency,
          value: majorAmount,
        },
        minorAmount: minorUnits.toString(),
        minorUnitDecimals: decimals,
        method: paymentMethod,
        occurredAt,
        reference,
        donor: req.body.donor ?? null,
        transaction: req.body.transaction ?? null,
        memo: req.body.purpose ?? null,
      },
    };

    const credential = buildCredential('DonationReceiptCredential', credentialSubject);
    const validation = await validateCredentialSubject(credentialSlug, credentialSubject);
    if (!validation.valid) {
      return res.status(400).json({
        error: 'invalid_credential_subject',
        message: 'Credential subject failed schema validation',
        details: validation.errors,
      });
    }

    const proofCreated = new Date().toISOString();
    const jws = await signCredential(credential);
    const credentialRecord = {
      id: crypto.randomUUID(),
      type: credentialSlug,
      subject: credentialSubject,
      vc: {
        credential,
        proof: { type: 'Ed25519Signature2020', created: proofCreated, jws },
      },
      issued_at: proofCreated,
      ledger_event_id: ledgerEvent.id,
    };

    await storeCredential(credentialRecord);
    await recordCredentialStatus({
      id: credentialRecord.id,
      type: credentialRecord.type,
      issued_at: credentialRecord.issued_at,
      ledger_event_id: credentialRecord.ledger_event_id,
      status: 'active',
    });

    const receiptPayload = {
      timestamp: occurredAt,
      ledger_event_id: ledgerEvent.id,
      vc_id: vcId,
      payment_method: paymentMethod,
      currency,
      amount_minor: minorUnits.toString(),
      amount_major: majorAmount,
      minor_unit_decimals: decimals,
      reference,
      donor: req.body.donor ?? null,
      transaction: req.body.transaction ?? null,
      metadata: req.body.metadata ?? {},
      proof_jws: jws,
    };
    await appendJsonl(receiptsLogPath, receiptPayload);

    const telemetryEvent = {
      event: 'donation_inflow',
      occurred_at: occurredAt,
      ledger_event_id: ledgerEvent.id,
      vc_id: vcId,
      currency,
      amount_minor: minorUnits.toString(),
      minor_unit_decimals: decimals,
      payment_method: paymentMethod,
      reference,
    };
    await appendJsonl(telemetryLogPath, telemetryEvent);

    res.status(201).json({
      vcId,
      ledgerEvent,
      credential,
      proof: credentialRecord.vc.proof,
      receipt: receiptPayload,
    });
  } catch (error) {
    next(error);
  }
});

app.post('/payouts/create', async (req, res, next) => {
  try {
    const registry = await loadTrustRegistry();
    const credentialSlug = 'ImpactPayoutCredential';
    if (!registry.recognizedCredentials?.includes(credentialSlug)) {
      return res.status(409).json({
        error: 'credential_not_recognized',
        message: `${credentialSlug} is not present in trust registry`,
      });
    }

    const currency = String(req.body.currency ?? '').toUpperCase();
    if (!currency) {
      return res.status(400).json({ error: 'currency is required' });
    }

    let minorUnits;
    try {
      minorUnits = parseMinorUnits(req.body, currency);
    } catch (error) {
      return res.status(400).json({ error: error.message });
    }

    let occurredAt;
    try {
      const occurredAtDate = req.body.occurred_at ? new Date(req.body.occurred_at) : new Date();
      if (Number.isNaN(occurredAtDate.getTime())) {
        throw new Error('invalid');
      }
      occurredAt = occurredAtDate.toISOString();
    } catch (error) {
      return res.status(400).json({ error: 'occurred_at must be a valid ISO-8601 timestamp' });
    }

    if (!req.body.beneficiary) {
      return res.status(400).json({ error: 'beneficiary is required' });
    }

    const vcId = `vc:impact:${crypto.randomUUID()}`;
    const reference = req.body.reference ?? vcId;
    const decimals = minorUnitDecimals(currency);
    const majorAmount = formatMajorAmount(minorUnits, currency);
    const tags = Array.isArray(req.body.tags) ? req.body.tags : [];

    const ledgerEvent = await recordLedgerEvent({
      direction: 'OUTFLOW',
      amount_cents: minorUnits.toString(),
      currency,
      purpose: req.body.purpose ?? 'Little Footsteps impact payout',
      source: req.body.source ?? 'impact:payout',
      occurred_at: occurredAt,
      beneficiary: req.body.beneficiary,
      tags: ['impact', 'payout', ...tags],
      vc_id: vcId,
      metadata: {
        ...(req.body.metadata ?? {}),
        reference,
        vendor: req.body.vendor ?? null,
        minor_unit_decimals: decimals,
        supporting_docs: req.body.supporting_docs ?? [],
      },
    });

    const credentialSubject = {
      payout: {
        ledgerEventId: ledgerEvent.id,
        amount: {
          currency,
          value: majorAmount,
        },
        minorAmount: minorUnits.toString(),
        minorUnitDecimals: decimals,
        beneficiary: req.body.beneficiary,
        vendor: req.body.vendor ?? null,
        purpose: req.body.purpose ?? 'Little Footsteps impact payout',
        occurredAt,
        reference,
        supportingDocs: req.body.supporting_docs ?? [],
        tags,
      },
    };

    const validation = await validateCredentialSubject(credentialSlug, credentialSubject);
    if (!validation.valid) {
      return res.status(400).json({
        error: 'invalid_credential_subject',
        message: 'Credential subject failed schema validation',
        details: validation.errors,
      });
    }

    const credential = buildCredential(credentialSlug, credentialSubject);
    const proofCreated = new Date().toISOString();
    const jws = await signCredential(credential);
    const credentialRecord = {
      id: crypto.randomUUID(),
      type: credentialSlug,
      subject: credentialSubject,
      vc: {
        credential,
        proof: { type: 'Ed25519Signature2020', created: proofCreated, jws },
      },
      issued_at: proofCreated,
      ledger_event_id: ledgerEvent.id,
    };

    await storeCredential(credentialRecord);
    await recordCredentialStatus({
      id: credentialRecord.id,
      type: credentialRecord.type,
      issued_at: credentialRecord.issued_at,
      ledger_event_id: credentialRecord.ledger_event_id,
      status: 'active',
    });

    const telemetryEvent = {
      event: 'impact_payout',
      occurred_at: occurredAt,
      ledger_event_id: ledgerEvent.id,
      vc_id: vcId,
      currency,
      amount_minor: minorUnits.toString(),
      minor_unit_decimals: decimals,
      beneficiary: req.body.beneficiary,
      tags,
    };
    await appendJsonl(telemetryLogPath, telemetryEvent);

    res.status(201).json({
      vcId,
      ledgerEvent,
      credential,
      proof: credentialRecord.vc.proof,
    });
  } catch (error) {
    next(error);
  }
});

app.post('/ledger/events', async (req, res, next) => {
  try {
    const { direction, amount_cents, currency } = req.body;
    if (!direction || amount_cents === undefined || amount_cents === null || !currency) {
      return res.status(400).json({ error: 'direction, amount_cents, and currency are required' });
    }
    let normalizedDirection;
    let normalizedAmount;
    try {
      normalizedDirection = validateLedgerDirection(direction);
      normalizedAmount = parseLedgerAmount(amount_cents);
    } catch (error) {
      return res.status(400).json({ error: error.message });
    }
    const normalizedCurrency = String(currency).toUpperCase();
    const saved = await recordLedgerEvent({
      direction: normalizedDirection,
      amount_cents: normalizedAmount.toString(),
      currency: normalizedCurrency,
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
    const totals = await fetchDailyTotals();
    res.json(totals);
  } catch (error) {
    next(error);
  }
});

app.get('/governance/amendments', async (_req, res, next) => {
  try {
    const amendments = await loadAmendments();
    res.json({ amendments });
  } catch (error) {
    next(error);
  }
});

app.get('/audit/trails', async (req, res, next) => {
  try {
    const limit = Number.parseInt(req.query.limit ?? '20', 10);
    const trail = await buildAuditTrail(Number.isFinite(limit) ? limit : 20);
    res.json(trail);
  } catch (error) {
    next(error);
  }
});

app.get('/schemas', async (_req, res, next) => {
  try {
    const schemas = await loadCredentialSchemas();
    res.json(
      [...schemas.entries()].map(([slug, record]) => ({
        slug,
        $id: record.schema.$id,
        title: record.schema.title,
        schema: record.schema,
      })),
    );
  } catch (error) {
    next(error);
  }
});

app.get('/schemas/:slug', async (req, res, next) => {
  try {
    const schemas = await loadCredentialSchemas();
    const record = schemas.get(req.params.slug);
    if (!record) {
      return res.status(404).json({ error: 'schema_not_found', message: 'Unknown credential schema' });
    }
    res.json(record.schema);
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

    const validation = await validateCredentialSubject(credentialSlug, credentialSubject);
    if (!validation.valid) {
      return res.status(400).json({
        error: 'invalid_credential_subject',
        message: 'Credential subject failed schema validation',
        details: validation.errors,
      });
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
    await recordCredentialStatus({
      id: credentialRecord.id,
      type: credentialRecord.type,
      issued_at: credentialRecord.issued_at,
      ledger_event_id: credentialRecord.ledger_event_id,
      status: 'active',
    });

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

app.get('/stream', (_req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    Connection: 'keep-alive',
    'Cache-Control': 'no-cache',
  });

  streamClients.add(res);
  res.write(`event: connected\ndata: {"status":"ok"}\n\n`);

  res.on('close', () => {
    streamClients.delete(res);
  });
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
