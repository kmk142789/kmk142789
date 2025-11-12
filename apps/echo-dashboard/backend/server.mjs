import express from 'express';
import cors from 'cors';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { promises as fs, createReadStream } from 'node:fs';
import process from 'node:process';
import { Pool } from 'pg';
import bs58check from 'bs58check';
import { parse as parseYaml, stringify as stringifyYaml } from 'yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '../../..');
export const LOG_DIRECTORY = join(repoRoot, 'logs');
export const PUZZLE_DIRECTORY = join(repoRoot, 'puzzle_solutions');
export const WHISPERVAULT_POLICY_PATH = process.env.WHISPERVAULT_POLICY_PATH
  ? resolve(repoRoot, process.env.WHISPERVAULT_POLICY_PATH)
  : join(repoRoot, 'whispervault', 'policies', 'spending_policy.yaml');
const CLI_ENTRYPOINT = join(repoRoot, 'echo_cli', 'main.py');
const CODEX_REGISTRY_PATH = join(repoRoot, 'codex', 'registry.json');
const PUZZLE_INDEX_PATH = join(repoRoot, 'data', 'puzzle_index.json');

const API_PORT = Number(process.env.ECHO_DASHBOARD_PORT || process.env.PORT || 5050);
const PYTHON_BIN = process.env.ECHO_DASHBOARD_PYTHON || process.env.PYTHON_BIN || 'python3';
const CLI_TIMEOUT_MS = Number(process.env.ECHO_DASHBOARD_TIMEOUT_MS || 45000);
const MAX_ARG_LENGTH = 128;
const MAX_ARGS = 16;
const DEFAULT_LOG_CHUNK_BYTES = 8192;
const MIN_LOG_CHUNK_BYTES = 512;
const MAX_LOG_CHUNK_BYTES = 262144;
const DEFAULT_POLICY_ID = 'whispervault-spending';

function normalisePolicyNumber(value) {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  const numeric = Number.parseFloat(value);
  if (!Number.isFinite(numeric) || numeric < 0) {
    return null;
  }
  return Number.isInteger(numeric) ? numeric : Number.parseFloat(numeric.toFixed(2));
}

async function readWhispervaultPolicyDocument() {
  try {
    const payload = await fs.readFile(WHISPERVAULT_POLICY_PATH, 'utf8');
    const parsed = parseYaml(payload) ?? {};
    const thresholds = parsed.thresholds ?? {};
    return {
      raw: parsed,
      id: typeof parsed.id === 'string' && parsed.id.trim() ? parsed.id.trim() : DEFAULT_POLICY_ID,
      thresholds: {
        selfApproveMax: normalisePolicyNumber(thresholds.self_approve_max) ?? 0,
        dualApproveMin: normalisePolicyNumber(thresholds.dual_approve_min) ?? 0,
        governanceMin: normalisePolicyNumber(thresholds.governance_min) ?? 0,
        cashWithdrawalCap: normalisePolicyNumber(thresholds.cash_withdrawal_cap) ?? 0,
      },
    };
  } catch (error) {
    if (error?.code !== 'ENOENT') {
      console.warn('Unable to read WhisperVault policy', error.message);
    }
    throw new Error('policy_read_failed');
  }
}

async function loadWhispervaultPolicy() {
  const document = await readWhispervaultPolicyDocument();
  return {
    id: document.id,
    selfApproveMax: document.thresholds.selfApproveMax,
    dualApproveMin: document.thresholds.dualApproveMin,
    governanceMin: document.thresholds.governanceMin,
    cashWithdrawalCap: document.thresholds.cashWithdrawalCap,
  };
}

function parsePolicyRequest(body = {}) {
  const id = typeof body.id === 'string' && body.id.trim() ? body.id.trim() : DEFAULT_POLICY_ID;
  const fields = [
    ['selfApproveMax', 'selfApproveMax'],
    ['dualApproveMin', 'dualApproveMin'],
    ['governanceMin', 'governanceMin'],
    ['cashWithdrawalCap', 'cashWithdrawalCap'],
  ];
  const result = { id };
  const invalid = [];
  for (const [sourceKey, targetKey] of fields) {
    const value = normalisePolicyNumber(body[sourceKey]);
    if (value === null) {
      invalid.push(sourceKey);
    } else {
      result[targetKey] = value;
    }
  }
  if (invalid.length > 0) {
    const error = new Error('invalid_policy_fields');
    error.fields = invalid;
    throw error;
  }
  return result;
}

async function writeWhispervaultPolicy(update) {
  const baseDocument = await readWhispervaultPolicyDocument().catch(() => ({
    raw: {},
    id: DEFAULT_POLICY_ID,
    thresholds: {
      selfApproveMax: 0,
      dualApproveMin: 0,
      governanceMin: 0,
      cashWithdrawalCap: 0,
    },
  }));
  const nextDocument = {
    ...baseDocument.raw,
    id: update.id || baseDocument.id || DEFAULT_POLICY_ID,
    thresholds: {
      ...(baseDocument.raw?.thresholds ?? {}),
      self_approve_max: update.selfApproveMax,
      dual_approve_min: update.dualApproveMin,
      governance_min: update.governanceMin,
      cash_withdrawal_cap: update.cashWithdrawalCap,
    },
  };
  await fs.mkdir(dirname(WHISPERVAULT_POLICY_PATH), { recursive: true });
  await fs.writeFile(WHISPERVAULT_POLICY_PATH, stringifyYaml(nextDocument, { lineWidth: 0 }));
  return {
    id: nextDocument.id || DEFAULT_POLICY_ID,
    selfApproveMax: update.selfApproveMax,
    dualApproveMin: update.dualApproveMin,
    governanceMin: update.governanceMin,
    cashWithdrawalCap: update.cashWithdrawalCap,
  };
}

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

function clampChunkSize(value = DEFAULT_LOG_CHUNK_BYTES) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    return DEFAULT_LOG_CHUNK_BYTES;
  }
  return Math.min(Math.max(parsed, MIN_LOG_CHUNK_BYTES), MAX_LOG_CHUNK_BYTES);
}

function normaliseCursor(cursor, size) {
  if (cursor === undefined || cursor === null || cursor === '' || cursor === 'latest') {
    return { mode: 'latest', value: size };
  }
  const parsed = Number.parseInt(cursor, 10);
  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error('invalid_cursor');
  }
  return { mode: 'explicit', value: Math.min(parsed, size) };
}

export async function readLogChunk(name, options = {}) {
  const safeName = sanitiseFilename(name);
  if (!safeName) {
    throw new Error('invalid_filename');
  }
  const absolute = resolve(LOG_DIRECTORY, safeName);
  if (!absolute.startsWith(LOG_DIRECTORY)) {
    throw new Error('invalid_path');
  }

  const stats = await fs.stat(absolute);
  if (!stats.isFile()) {
    throw new Error('not_found');
  }

  const size = stats.size;
  const limit = clampChunkSize(options.limit);
  const direction = options.direction === 'backward' ? 'backward' : 'forward';
  const cursor = normaliseCursor(options.cursor, size);

  let start = 0;
  let end = 0;
  if (cursor.mode === 'latest') {
    end = size;
    start = Math.max(0, size - limit);
  } else if (direction === 'backward') {
    end = cursor.value;
    start = Math.max(0, end - limit);
  } else {
    start = cursor.value;
    end = Math.min(start + limit, size);
  }

  const length = Math.max(0, end - start);
  let chunk = '';
  if (length > 0) {
    const handle = await fs.open(absolute, 'r');
    try {
      const buffer = Buffer.alloc(length);
      const { bytesRead } = await handle.read(buffer, 0, length, start);
      chunk = buffer.subarray(0, bytesRead).toString('utf8');
    } finally {
      await handle.close();
    }
  }

  return {
    name: safeName,
    chunk,
    start,
    end,
    size,
    hasMoreBackward: start > 0,
    hasMoreForward: end < size,
    previousCursor: start > 0 ? start : null,
    nextCursor: end < size ? end : null,
  };
}

function coerceDate(value) {
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }
  if (typeof value === 'number') {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }
  if (typeof value === 'string') {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }
  return null;
}

function truncateToDay(date) {
  const utc = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
  return new Date(utc);
}

function bucketSeries(dates) {
  const buckets = new Map();
  for (const date of dates) {
    if (!(date instanceof Date)) continue;
    const bucket = truncateToDay(date).toISOString();
    buckets.set(bucket, (buckets.get(bucket) || 0) + 1);
  }
  return Array.from(buckets.entries())
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([ts, value]) => ({ ts, value }));
}

async function gatherFileStats(directory) {
  try {
    const entries = await fs.readdir(directory, { withFileTypes: true });
    const results = [];
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      const absolute = resolve(directory, entry.name);
      const stats = await fs.stat(absolute);
      results.push({ name: entry.name, path: absolute, mtime: stats.mtime });
    }
    return results;
  } catch (error) {
    console.warn(`Unable to scan directory ${directory}`, error.message);
    return [];
  }
}

async function countFileLines(path) {
  return new Promise((resolve) => {
    const stream = createReadStream(path, { encoding: 'utf8' });
    let count = 0;
    let remainder = '';
    stream.on('data', (chunk) => {
      const segments = (remainder + chunk).split(/\r?\n/);
      remainder = segments.pop() || '';
      count += segments.length;
    });
    stream.on('end', () => {
      if (remainder) {
        count += 1;
      }
      resolve(count);
    });
    stream.on('error', () => resolve(0));
  });
}

function withinRange(date, from, to) {
  const value = coerceDate(date);
  if (!value) return false;
  const time = value.getTime();
  return time >= from.getTime() && time <= to.getTime();
}

export function parseRangeQuery(query = {}) {
  const toCandidate = coerceDate(query.to) || new Date();
  const rangePreset = typeof query.range === 'string' ? query.range : '24h';
  const presetDurations = new Map([
    ['24h', 24 * 60 * 60 * 1000],
    ['7d', 7 * 24 * 60 * 60 * 1000],
    ['30d', 30 * 24 * 60 * 60 * 1000],
  ]);
  let fromCandidate = coerceDate(query.from);
  if (!fromCandidate) {
    const duration = presetDurations.get(rangePreset) || presetDurations.get('24h');
    fromCandidate = new Date(toCandidate.getTime() - duration);
  }

  if (Number.isNaN(fromCandidate.getTime()) || Number.isNaN(toCandidate.getTime())) {
    throw new Error('invalid_range');
  }
  if (fromCandidate.getTime() > toCandidate.getTime()) {
    throw new Error('invalid_range');
  }
  return { from: fromCandidate, to: toCandidate };
}

export async function loadMetricsOverview({ from, to }) {
  const codexItems = await listCodexItems();
  const codexDates = codexItems
    .map((item) => coerceDate(item?.merged_at))
    .filter((date) => date && withinRange(date, from, to));
  const codexSeries = bucketSeries(codexDates);

  const puzzleFiles = await gatherFileStats(PUZZLE_DIRECTORY);
  const filteredPuzzles = puzzleFiles.filter((file) => withinRange(file.mtime, from, to));
  const puzzleSeries = bucketSeries(filteredPuzzles.map((file) => file.mtime));

  const logFiles = await gatherFileStats(LOG_DIRECTORY);
  const filteredLogs = logFiles.filter((file) => withinRange(file.mtime, from, to));
  let logTotal = 0;
  const logBuckets = new Map();
  for (const file of filteredLogs) {
    const lines = await countFileLines(file.path);
    logTotal += lines;
    const bucket = truncateToDay(file.mtime).toISOString();
    logBuckets.set(bucket, (logBuckets.get(bucket) || 0) + lines);
  }
  const logSeries = Array.from(logBuckets.entries())
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([ts, value]) => ({ ts, value }));

  let attestation = null;
  if (pool) {
    await ensurePuzzleAttestationTable();
    const result = await pool.query(
      `select date_trunc('day', created_at) as bucket, count(*)::int as value
       from puzzle_attestations
       where created_at between $1 and $2
       group by bucket
       order by bucket asc`,
      [from.toISOString(), to.toISOString()]
    );
    const series = result.rows.map((row) => {
      const value = Number.parseInt(row.value, 10);
      const safeValue = Number.isNaN(value) ? 0 : value;
      return {
        ts: new Date(row.bucket).toISOString(),
        value: safeValue,
      };
    });
    const total = series.reduce((sum, entry) => sum + entry.value, 0);
    attestation = {
      label: 'Stored Attestations',
      total,
      series,
    };
  }

  return {
    range: { from: from.toISOString(), to: to.toISOString() },
    metrics: {
      codexMerges: { label: 'Codex merges', total: codexDates.length, series: codexSeries },
      puzzleSolutions: { label: 'Puzzle solutions', total: filteredPuzzles.length, series: puzzleSeries },
      logVolume: { label: 'Log entries', total: logTotal, series: logSeries },
      attestationStored: attestation,
    },
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

export const app = express();
app.use(cors());
app.use(express.json({ limit: '1mb' }));

app.get('/whispervault/policy', async (_req, res) => {
  try {
    const policy = await loadWhispervaultPolicy();
    res.json({ policy });
  } catch (error) {
    const status = error.message === 'policy_read_failed' ? 500 : 500;
    res.status(status).json({ error: error.message || 'policy_read_failed' });
  }
});

app.put('/whispervault/policy', async (req, res) => {
  try {
    const payload = parsePolicyRequest(req.body || {});
    const policy = await writeWhispervaultPolicy(payload);
    res.json({ policy });
  } catch (error) {
    if (error.message === 'invalid_policy_fields') {
      res.status(400).json({ error: error.message, fields: error.fields || [] });
      return;
    }
    res.status(500).json({ error: 'policy_write_failed' });
  }
});

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

app.get('/logs/:name/chunk', async (req, res) => {
  try {
    const payload = await readLogChunk(req.params.name, req.query || {});
    res.json(payload);
  } catch (error) {
    if (error?.code === 'ENOENT' || error.message === 'not_found') {
      res.status(404).json({ error: 'not_found' });
      return;
    }
    const status = ['invalid_filename', 'invalid_path', 'invalid_cursor'].includes(error.message)
      ? 400
      : 500;
    res.status(status).json({ error: error.message });
  }
});

app.get('/logs/:name', async (req, res) => {
  try {
    const payload = await readFilePreview(LOG_DIRECTORY, req.params.name);
    res.json(payload);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/metrics/overview', async (req, res) => {
  try {
    const range = parseRangeQuery(req.query || {});
    const payload = await loadMetricsOverview(range);
    res.json(payload);
  } catch (error) {
    const status = error.message === 'invalid_range' ? 400 : 500;
    res.status(status).json({ error: error.message });
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

if (process.argv[1] === __filename) {
  app.listen(API_PORT, () => {
    console.log(`Echo dashboard API listening on http://localhost:${API_PORT}`);
  });
}
