import 'dotenv/config';
import express from 'express';
import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
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

const receiptsLogPath =
  process.env.DONATION_RECEIPTS_LOG_PATH ?? 'state/little_footsteps/donation_receipts.jsonl';
const telemetryLogPath =
  process.env.DONATION_TELEMETRY_LOG_PATH ?? 'state/little_footsteps/dashboard/donations.jsonl';

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
        ledger_event_id UUID REFERENCES ledger_events(id) ON DELETE SET NULL
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
    return { ...event, amount_cents: amountMinor.toString(), id, occurred_at: occurredAt };
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

async function appendJsonl(logPath, payload) {
  const resolved = path.resolve(logPath);
  await fs.mkdir(path.dirname(resolved), { recursive: true });
  await fs.appendFile(resolved, `${JSON.stringify(payload)}\n`, { encoding: 'utf8' });
}

app.get('/healthz', (_req, res) => {
  res.json({ status: 'ok', issuer: issuerDid });
});

app.post('/donations/intake', async (req, res, next) => {
  try {
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
    const proofCreated = new Date().toISOString();
    const jws = await signCredential(credential);
    const credentialRecord = {
      id: crypto.randomUUID(),
      type: 'DonationReceiptCredential',
      subject: credentialSubject,
      vc: {
        credential,
        proof: { type: 'Ed25519Signature2020', created: proofCreated, jws },
      },
      issued_at: proofCreated,
      ledger_event_id: ledgerEvent.id,
    };

    await storeCredential(credentialRecord);

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
      const inflows = BigInt(rows[0].inflows ?? 0);
      const outflows = BigInt(rows[0].outflows ?? 0);
      res.json({
        inflows: inflows.toString(),
        outflows: outflows.toString(),
        net: (inflows - outflows).toString(),
      });
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
