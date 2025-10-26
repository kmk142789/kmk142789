import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import fs from 'fs/promises';
import { watch } from 'fs';
import path from 'path';
import EventEmitter from 'events';
import crypto from 'node:crypto';

const app = express();
const emitter = new EventEmitter();

const ledgerPath = path.resolve(process.env.LEDGER_PATH ?? 'ledger/little_footsteps_bank.jsonl');
const proofsDir = path.resolve(process.env.PROOFS_DIR ?? 'proofs/little_footsteps_bank');
const continuityPath = path.resolve(process.env.CONTINUITY_LOG ?? 'state/continuity/multisig_recovery.jsonl');
const amendmentsPath = path.resolve(process.env.AMENDMENTS_PATH ?? 'data/governance/amendments.json');

app.use(cors());
app.use(express.json());

function amountToCents(amount) {
  if (typeof amount === 'number' && Number.isFinite(amount)) {
    return Math.round(amount * 100);
  }
  const text = String(amount ?? '0');
  const sign = text.startsWith('-') ? -1 : 1;
  const [wholePart, fractionPart = ''] = text.replace('-', '').split('.');
  const cents = (fractionPart.padEnd(2, '0').slice(0, 2));
  return sign * (parseInt(wholePart || '0', 10) * 100 + parseInt(cents || '0', 10));
}

async function loadLedgerEvents() {
  try {
    const contents = await fs.readFile(ledgerPath, 'utf8');
    const events = [];
    for (const line of contents.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const payload = JSON.parse(trimmed);
        events.push(payload);
      } catch (error) {
        console.warn('Skipping malformed ledger line', error);
      }
    }
    return events;
  } catch (error) {
    if (error.code === 'ENOENT') {
      return [];
    }
    throw error;
  }
}

async function loadContinuityEvents() {
  try {
    const contents = await fs.readFile(continuityPath, 'utf8');
    const items = [];
    for (const line of contents.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        items.push(JSON.parse(trimmed));
      } catch (error) {
        console.warn('Skipping malformed continuity checkpoint', error);
      }
    }
    return items;
  } catch (error) {
    if (error.code === 'ENOENT') {
      return [];
    }
    throw error;
  }
}

function normaliseEvent(entry) {
  const direction = (entry.direction ?? 'inflow').toUpperCase();
  const amountCents = amountToCents(entry.amount ?? 0);
  const seq = typeof entry.seq === 'number' ? entry.seq : null;
  const id = `ledger-${seq ?? entry.digest ?? crypto.randomUUID()}`;
  const narrative = entry.narrative ?? '';
  const base = {
    id,
    seq,
    direction,
    amount_cents: amountCents,
    currency: entry.asset ?? 'USD',
    occurred_at: entry.timestamp ?? new Date().toISOString(),
    narrative,
    source: direction === 'INFLOW' ? entry.account : null,
    purpose: direction === 'OUTFLOW' ? narrative : null,
    beneficiary: direction === 'OUTFLOW' ? entry.account : null,
    digest: entry.digest,
    proof_path: Number.isInteger(seq)
      ? path.join(proofsDir, `entry_${String(seq).padStart(5, '0')}.json`)
      : null,
    ots_receipt: entry.ots_receipt ?? null,
  };
  return base;
}

async function computeTotals(events) {
  return events.reduce(
    (acc, event) => {
      const cents = amountToCents(event.amount ?? 0);
      if ((event.direction ?? '').toLowerCase() === 'inflow') {
        acc.inflows += cents;
      } else {
        acc.outflows += cents;
      }
      acc.net = acc.inflows - acc.outflows;
      return acc;
    },
    { inflows: 0, outflows: 0, net: 0 },
  );
}

async function readAmendments() {
  try {
    const text = await fs.readFile(amendmentsPath, 'utf8');
    const parsed = JSON.parse(text);
    return parsed.amendments ?? [];
  } catch (error) {
    if (error.code === 'ENOENT') {
      return [];
    }
    console.warn('Unable to load amendments', error);
    return [];
  }
}

async function buildAuditTrail(limit = 20) {
  const [events, checkpoints] = await Promise.all([
    loadLedgerEvents(),
    loadContinuityEvents(),
  ]);
  const trail = events
    .slice(-limit)
    .map((entry) => ({
      seq: entry.seq,
      digest: entry.digest,
      direction: entry.direction,
      amount: entry.amount,
      asset: entry.asset,
      timestamp: entry.timestamp,
      proof_path: path.join(proofsDir, `entry_${String(entry.seq).padStart(5, '0')}.json`),
      ots_receipt: entry.ots_receipt ?? null,
    }))
    .reverse();
  return { ledger: trail, continuity: checkpoints.slice(-limit).reverse() };
}

app.get('/metrics/totals', async (_req, res) => {
  const events = await loadLedgerEvents();
  const totals = await computeTotals(events);
  res.json(totals);
});

app.get('/ledger/events', async (req, res) => {
  const limit = Number.parseInt(req.query.limit ?? '50', 10);
  const events = await loadLedgerEvents();
  const normalised = events.map(normaliseEvent).reverse();
  res.json(normalised.slice(0, Number.isFinite(limit) ? limit : 50));
});

app.get('/governance/amendments', async (_req, res) => {
  const amendments = await readAmendments();
  res.json({ amendments });
});

app.get('/audit/trails', async (req, res) => {
  const limit = Number.parseInt(req.query.limit ?? '20', 10);
  const trail = await buildAuditTrail(Number.isFinite(limit) ? limit : 20);
  res.json(trail);
});

app.get('/stream', async (_req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const sendLedgerEvent = async () => {
    const events = await loadLedgerEvents();
    if (events.length === 0) {
      return;
    }
    const latest = events[events.length - 1];
    const payload = {
      entry: normaliseEvent(latest),
      totals: await computeTotals(events),
    };
    res.write(`event: ledger\n`);
    res.write(`data: ${JSON.stringify(payload)}\n\n`);
  };

  const listener = () => {
    sendLedgerEvent().catch((error) => console.error('stream error', error));
  };

  emitter.on('ledger-update', listener);
  res.write(`event: heartbeat\n`);
  res.write(`data: {"status":"connected"}\n\n`);

  sendLedgerEvent().catch((error) => console.error('initial stream error', error));

  req.on('close', () => {
    emitter.off('ledger-update', listener);
    res.end();
  });
});

async function bootstrapWatcher() {
  try {
    await fs.access(ledgerPath);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
  watch(ledgerPath, { persistent: false }, () => {
    emitter.emit('ledger-update');
  });
}

const port = Number.parseInt(process.env.PORT ?? '4000', 10);
bootstrapWatcher().catch((error) => console.error('Watcher bootstrap failed', error));

app.listen(port, () => {
  console.log(JSON.stringify({
    event: 'transparency.bank.api.ready',
    port,
    ledgerPath,
    proofsDir,
    continuityPath,
    timestamp: new Date().toISOString(),
  }));
});
