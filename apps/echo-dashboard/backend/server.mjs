import express from 'express';
import cors from 'cors';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { promises as fs } from 'node:fs';
import process from 'node:process';
import { Pool } from 'pg';
import bs58check from 'bs58check';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '../../..');
const LOG_DIRECTORY = join(repoRoot, 'logs');
const PUZZLE_DIRECTORY = join(repoRoot, 'puzzle_solutions');
const CLI_ENTRYPOINT = join(repoRoot, 'echo_cli', 'main.py');
const CODEX_REGISTRY_PATH = join(repoRoot, 'codex', 'registry.json');
const PUZZLE_INDEX_PATH = join(repoRoot, 'data', 'puzzle_index.json');

const API_PORT = Number(process.env.ECHO_DASHBOARD_PORT || process.env.PORT || 5050);
const PYTHON_BIN = process.env.ECHO_DASHBOARD_PYTHON || process.env.PYTHON_BIN || 'python3';
const CLI_TIMEOUT_MS = Number(process.env.ECHO_DASHBOARD_TIMEOUT_MS || 45000);
const MAX_ARG_LENGTH = 128;
const MAX_ARGS = 16;

const ALLOWED_CLI_COMMANDS = new Map([
  ['refresh', { label: 'Refresh Atlas', defaultArgs: ['--json'] }],
  ['verify', { label: 'Verify Puzzles', defaultArgs: ['--json'] }],
  ['stats', { label: 'Puzzle Stats', defaultArgs: ['--json'] }],
  ['enrich-ud', { label: 'Enrich UD Records', defaultArgs: ['--json'] }],
  ['export', { label: 'Export Puzzle Data', defaultArgs: ['--json'] }],
  ['transcend', { label: 'Run Transcend Ritual', defaultArgs: ['--json'] }],
]);

const DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;
let pool = null;
if (DATABASE_URL) {
  pool = new Pool({
    connectionString: DATABASE_URL,
    ssl: process.env.PGSSLMODE === 'disable' ? false : { rejectUnauthorized: false },
    max: 5,
  });
}

async function ensureNeonTable() {
  if (!pool) return;
  await pool.query(`
    create table if not exists echo_dashboard_neon_keys (
      id uuid primary key,
      label text not null,
      encrypted_key text not null,
      last_four text not null,
      created_at timestamptz not null default now()
    )
  `);
}

function deriveEncryptionKey() {
  const rawKey = process.env.NEON_KEY_ENCRYPTION_KEY;
  if (!rawKey || rawKey.length < 16) {
    throw new Error('invalid_encryption_key');
  }
  return crypto.createHash('sha256').update(rawKey).digest();
}

function encryptSecret(secret) {
  const key = deriveEncryptionKey();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  const encrypted = Buffer.concat([cipher.update(secret, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `${iv.toString('base64')}.${encrypted.toString('base64')}.${tag.toString('base64')}`;
}

function sanitiseFilename(input) {
  if (typeof input !== 'string') return null;
  const normalised = input.trim();
  if (!/^[a-zA-Z0-9._-]+$/.test(normalised)) {
    return null;
  }
  return normalised;
}

async function listMarkdown(directory) {
  try {
    const entries = await fs.readdir(directory, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile() && /\.(md|log)$/i.test(entry.name))
      .map((entry) => entry.name)
      .sort();
  } catch (error) {
    console.warn(`Unable to list ${directory}`, error.message);
    return [];
  }
}

async function readFilePreview(directory, filename) {
  const safeName = sanitiseFilename(filename);
  if (!safeName) {
    throw new Error('invalid_filename');
  }
  const absolute = resolve(directory, safeName);
  if (!absolute.startsWith(directory)) {
    throw new Error('invalid_path');
  }
  const payload = await fs.readFile(absolute, 'utf8');
  const lines = payload.split(/\r?\n/);
  return {
    name: safeName,
    preview: lines.slice(0, 40).join('\n'),
    content: payload,
  };
}

async function runCliCommand(command, args = []) {
  if (!ALLOWED_CLI_COMMANDS.has(command)) {
    throw new Error('command_not_allowed');
  }
  const safeArgs = [];
  for (const value of args) {
    if (typeof value !== 'string') continue;
    const trimmed = value.trim();
    if (!trimmed) continue;
    if (trimmed.length > MAX_ARG_LENGTH) {
      throw new Error('argument_too_long');
    }
    safeArgs.push(trimmed);
    if (safeArgs.length >= MAX_ARGS) break;
  }

  const defaults = ALLOWED_CLI_COMMANDS.get(command)?.defaultArgs || [];
  const finalArgs = [...defaults.filter((item) => !safeArgs.includes(item)), ...safeArgs];

  return new Promise((resolve, reject) => {
    const child = spawn(PYTHON_BIN, [CLI_ENTRYPOINT, command, ...finalArgs], {
      cwd: repoRoot,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });

    let stdout = '';
    let stderr = '';
    let finished = false;

    const timeout = setTimeout(() => {
      if (finished) return;
      finished = true;
      child.kill('SIGKILL');
      reject(new Error('cli_timeout'));
    }, CLI_TIMEOUT_MS);

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString('utf8');
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString('utf8');
    });

    child.on('error', (error) => {
      if (finished) return;
      finished = true;
      clearTimeout(timeout);
      reject(error);
    });

    child.on('close', (code) => {
      if (finished) return;
      finished = true;
      clearTimeout(timeout);
      resolve({ code, stdout, stderr });
    });
  });
}

async function listNeonKeys() {
  if (!pool) {
    throw new Error('database_unconfigured');
  }
  await ensureNeonTable();
  const result = await pool.query(
    'select id, label, last_four, created_at from echo_dashboard_neon_keys order by created_at desc'
  );
  return result.rows;
}

async function insertNeonKey(label, value) {
  if (!pool) {
    throw new Error('database_unconfigured');
  }
  await ensureNeonTable();
  const trimmedLabel = label?.trim();
  const trimmedValue = value?.trim();
  if (!trimmedLabel) {
    throw new Error('label_required');
  }
  if (!trimmedValue) {
    throw new Error('value_required');
  }
  if (trimmedValue.length < 20) {
    throw new Error('value_too_short');
  }
  const lastFour = trimmedValue.slice(-4);
  const encrypted = encryptSecret(trimmedValue);
  const id = crypto.randomUUID();
  const result = await pool.query(
    'insert into echo_dashboard_neon_keys (id, label, encrypted_key, last_four) values ($1, $2, $3, $4) returning id, label, last_four, created_at',
    [id, trimmedLabel, encrypted, lastFour]
  );
  return result.rows[0];
}

async function deleteNeonKey(id) {
  if (!pool) {
    throw new Error('database_unconfigured');
  }
  await ensureNeonTable();
  await pool.query('delete from echo_dashboard_neon_keys where id = $1', [id]);
}

function stableJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableJson(item)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

let cachedPuzzleIndex = null;

async function loadPuzzleIndex() {
  if (cachedPuzzleIndex) {
    return cachedPuzzleIndex;
  }
  try {
    const payload = JSON.parse(await fs.readFile(PUZZLE_INDEX_PATH, 'utf8'));
    const entries = new Map();
    for (const item of payload?.puzzles || []) {
      const id = Number.parseInt(item?.id, 10);
      if (Number.isFinite(id)) {
        entries.set(id, item);
      }
    }
    cachedPuzzleIndex = { raw: payload, entries };
  } catch (error) {
    console.warn('Unable to load puzzle index', error.message);
    cachedPuzzleIndex = { raw: { puzzles: [] }, entries: new Map() };
  }
  return cachedPuzzleIndex;
}

function extractPuzzleId(name) {
  if (!name) return null;
  const match = String(name).match(/(\d{1,5})/);
  if (!match) return null;
  const value = Number.parseInt(match[1], 10);
  return Number.isFinite(value) ? value : null;
}

async function ensurePuzzleAttestationTable() {
  if (!pool) return;
  await pool.query(`
    create table if not exists puzzle_attestations (
      id uuid primary key,
      puzzle_id integer not null,
      payload jsonb not null,
      checksum text not null,
      base58 text not null,
      ts timestamptz not null,
      record_hash text not null,
      created_at timestamptz not null default now()
    )
  `);
  await pool.query(
    'create unique index if not exists puzzle_attestations_record_hash_idx on puzzle_attestations(record_hash)'
  );
  await pool.query(
    'create index if not exists puzzle_attestations_puzzle_idx on puzzle_attestations(puzzle_id, created_at desc)'
  );
}

function computePuzzleAttestation(puzzleId, entry, content = '') {
  const payload = {
    title: entry?.title || `Puzzle #${puzzleId}`,
    address: entry?.address || null,
    script_type: entry?.script_type || null,
    hash160: entry?.hash160 || null,
  };
  if (content) {
    payload.content_digest = crypto.createHash('sha256').update(content, 'utf8').digest('hex');
  }
  const payloadJson = stableJson(payload);
  const checksum = crypto.createHash('sha256').update(payloadJson).digest('hex');
  const checksumBytes = Buffer.from(checksum, 'hex');
  const base58 = bs58check.encode(Buffer.concat([Buffer.from([0x00]), checksumBytes.subarray(0, 20)]));
  const record = {
    puzzle_id: puzzleId,
    payload,
    checksum,
    base58,
    ts: new Date().toISOString(),
  };
  const recordHash = crypto.createHash('sha256').update(stableJson(record)).digest('hex');
  return { record, recordHash };
}

async function upsertPuzzleAttestation(record, recordHash) {
  if (!pool) return null;
  await ensurePuzzleAttestationTable();
  const result = await pool.query(
    `insert into puzzle_attestations (id, puzzle_id, payload, checksum, base58, ts, record_hash)
     values ($1, $2, $3::jsonb, $4, $5, $6, $7)
     on conflict (record_hash) do update set
       payload = excluded.payload,
       checksum = excluded.checksum,
       base58 = excluded.base58,
       ts = excluded.ts,
       puzzle_id = excluded.puzzle_id
     returning puzzle_id, payload, checksum, base58, ts, record_hash, created_at`,
    [
      crypto.randomUUID(),
      record.puzzle_id,
      JSON.stringify(record.payload),
      record.checksum,
      record.base58,
      record.ts,
      recordHash,
    ]
  );
  const row = result.rows[0];
  if (!row) return null;
  return {
    puzzle_id: row.puzzle_id,
    payload: typeof row.payload === 'string' ? JSON.parse(row.payload) : row.payload,
    checksum: row.checksum,
    base58: row.base58,
    ts: row.ts,
    record_hash: row.record_hash,
    created_at: row.created_at,
    stored: true,
  };
}

async function fetchLatestPuzzleAttestation(puzzleId) {
  if (!pool) return null;
  await ensurePuzzleAttestationTable();
  const result = await pool.query(
    `select puzzle_id, payload, checksum, base58, ts, record_hash, created_at
     from puzzle_attestations
     where puzzle_id = $1
     order by created_at desc
     limit 1`,
    [puzzleId]
  );
  const row = result.rows[0];
  if (!row) return null;
  return {
    puzzle_id: row.puzzle_id,
    payload: typeof row.payload === 'string' ? JSON.parse(row.payload) : row.payload,
    checksum: row.checksum,
    base58: row.base58,
    ts: row.ts,
    record_hash: row.record_hash,
    created_at: row.created_at,
    stored: true,
  };
}

async function readCodexRegistry() {
  try {
    const payload = JSON.parse(await fs.readFile(CODEX_REGISTRY_PATH, 'utf8'));
    if (payload && typeof payload === 'object') {
      return payload;
    }
  } catch (error) {
    console.warn('Unable to read codex registry', error.message);
  }
  return { version: 1, generated_at: new Date().toISOString(), items: [] };
}

async function listCodexItems(limit = null) {
  const payload = await readCodexRegistry();
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (limit && Number.isFinite(limit)) {
    return items.slice(0, Number(limit));
  }
  return items;
}

async function solvePuzzle(puzzleId, content = '') {
  const { entries } = await loadPuzzleIndex();
  const entry = entries.get(Number(puzzleId));
  if (!entry) {
    return {
      puzzle: null,
      attestation: null,
      logs: [`Puzzle ${puzzleId} not found in index.`],
    };
  }

  const logs = [`Loaded puzzle ${puzzleId} (${entry.title || 'Untitled'})`];
  const { record, recordHash } = computePuzzleAttestation(puzzleId, entry, content);
  let attestation = null;
  try {
    const stored = await upsertPuzzleAttestation(record, recordHash);
    if (stored) {
      attestation = stored;
      logs.push('Attestation stored in Neon.');
    }
  } catch (error) {
    logs.push(`Failed to persist attestation: ${error.message}`);
    attestation = { ...record, record_hash: recordHash, stored: false };
  }
  if (!attestation) {
    attestation = { ...record, record_hash: recordHash, stored: false };
  }
  return {
    puzzle: entry,
    attestation,
    logs,
  };
}

const ASSISTANT_FUNCTIONS = {
  async solve_puzzle(args) {
    const puzzleId = Number.parseInt(args?.id ?? args?.puzzle_id, 10);
    if (!Number.isFinite(puzzleId)) {
      return {
        success: false,
        message: 'Puzzle id is required.',
        data: null,
        logs: ['Missing puzzle id in request.'],
      };
    }
    const result = await solvePuzzle(puzzleId);
    if (!result.puzzle) {
      return {
        success: false,
        message: `Puzzle ${puzzleId} not found in index.`,
        data: null,
        logs: result.logs,
      };
    }
    return {
      success: true,
      message: `Puzzle ${puzzleId}: ${result.puzzle.address}`,
      data: {
        puzzle: result.puzzle,
        attestation: result.attestation,
      },
      logs: result.logs,
    };
  },
  async echo_bank_start() {
    return {
      success: true,
      message: 'Launch echo.bank by installing dependencies and starting the dev server.',
      data: {
        commands: ['npm install', 'npm run dev'],
        path: join(repoRoot, 'apps', 'transparency.bank'),
      },
      logs: ['Provided echo.bank launch instructions.'],
    };
  },
  async list_codex(args) {
    const limit = Number.parseInt(args?.limit ?? args?.count ?? 10, 10);
    const items = await listCodexItems(Number.isFinite(limit) ? limit : undefined);
    return {
      success: true,
      message: `Listing ${items.length} codex entries`,
      data: { items },
      logs: [`Loaded ${items.length} entries from registry.`],
    };
  },
};

function routeAssistantMessage(message) {
  const normalised = String(message || '').toLowerCase();
  const puzzleMatch = normalised.match(/puzzle\s*#?\s*(\d+)/);
  if (puzzleMatch) {
    return { name: 'solve_puzzle', args: { id: puzzleMatch[1] } };
  }
  if (normalised.includes('echo bank')) {
    return { name: 'echo_bank_start', args: {} };
  }
  const limitMatch = normalised.match(/codex.*?(\d+)/);
  if (limitMatch) {
    return { name: 'list_codex', args: { limit: limitMatch[1] } };
  }
  if (normalised.includes('codex')) {
    return { name: 'list_codex', args: {} };
  }
  return { name: 'list_codex', args: { limit: 5 } };
}

const app = express();
app.use(cors());
app.use(express.json({ limit: '1mb' }));

app.get('/health', async (_req, res) => {
  try {
    if (pool) {
      await ensureNeonTable();
    }
    res.json({ ok: true, database: Boolean(pool) });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.get('/logs', async (_req, res) => {
  const files = await listMarkdown(LOG_DIRECTORY);
  res.json({ files });
});

app.get('/logs/:name', async (req, res) => {
  try {
    const payload = await readFilePreview(LOG_DIRECTORY, req.params.name);
    res.json(payload);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/puzzles', async (_req, res) => {
  const files = await listMarkdown(PUZZLE_DIRECTORY);
  res.json({ files });
});

app.get('/puzzles/:name', async (req, res) => {
  try {
    const descriptor = await readFilePreview(PUZZLE_DIRECTORY, req.params.name);
    const puzzleId = extractPuzzleId(descriptor.name);
    let attestation = null;
    if (puzzleId) {
      const existing = await fetchLatestPuzzleAttestation(puzzleId);
      if (existing) {
        attestation = existing;
      } else {
        const { attestation: computed } = await solvePuzzle(puzzleId, descriptor.content || descriptor.preview || '');
        attestation = computed;
      }
    }
    res.json({ ...descriptor, puzzle_id: puzzleId, attestation });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/api/codex', async (_req, res) => {
  const payload = await readCodexRegistry();
  res.json(payload);
});

app.post('/assistant/chat', async (req, res) => {
  try {
    const { message, function: functionName, args } = req.body || {};
    const call = functionName
      ? { name: functionName, args: args || {} }
      : routeAssistantMessage(message);
    const handler = ASSISTANT_FUNCTIONS[call.name];
    if (!handler) {
      res.status(400).json({ error: 'unknown_function' });
      return;
    }
    const result = await handler(call.args || {});
    res.json({
      success: result.success,
      message: result.message,
      function: call.name,
      arguments: call.args,
      data: result.data,
      logs: result.logs,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/cli/commands', (_req, res) => {
  const commands = Array.from(ALLOWED_CLI_COMMANDS.entries()).map(([value, meta]) => ({
    value,
    label: meta.label,
  }));
  res.json({ commands });
});

app.post('/cli/run', async (req, res) => {
  try {
    const { command, args } = req.body || {};
    const result = await runCliCommand(command, Array.isArray(args) ? args : []);
    res.json(result);
  } catch (error) {
    const status = error.message === 'command_not_allowed' ? 403 : 400;
    res.status(status).json({ error: error.message });
  }
});

app.get('/neon/keys', async (_req, res) => {
  try {
    const keys = await listNeonKeys();
    res.json({ keys });
  } catch (error) {
    if (error.message === 'database_unconfigured') {
      res.status(503).json({ error: 'database_unconfigured' });
      return;
    }
    res.status(500).json({ error: error.message });
  }
});

app.post('/neon/keys', async (req, res) => {
  try {
    const { label, value } = req.body || {};
    const key = await insertNeonKey(label, value);
    res.status(201).json({ key });
  } catch (error) {
    if (error.message === 'database_unconfigured') {
      res.status(503).json({ error: error.message });
      return;
    }
    const status = ['label_required', 'value_required', 'value_too_short', 'invalid_encryption_key'].includes(
      error.message
    )
      ? 400
      : 500;
    res.status(status).json({ error: error.message });
  }
});

app.delete('/neon/keys/:id', async (req, res) => {
  try {
    await deleteNeonKey(req.params.id);
    res.status(204).end();
  } catch (error) {
    if (error.message === 'database_unconfigured') {
      res.status(503).json({ error: error.message });
      return;
    }
    res.status(500).json({ error: error.message });
  }
});

app.use((req, res) => {
  res.status(404).json({ error: 'not_found' });
});

app.listen(API_PORT, () => {
  console.log(`Echo dashboard API listening on http://localhost:${API_PORT}`);
});
