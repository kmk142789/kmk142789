import express from 'express';
import cors from 'cors';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { promises as fs } from 'node:fs';
import process from 'node:process';
import { Pool } from 'pg';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '../../..');
const LOG_DIRECTORY = join(repoRoot, 'logs');
const PUZZLE_DIRECTORY = join(repoRoot, 'puzzle_solutions');
const CLI_ENTRYPOINT = join(repoRoot, 'echo_cli', 'main.py');

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

let pool = null;
if (process.env.NEON_DATABASE_URL) {
  pool = new Pool({
    connectionString: process.env.NEON_DATABASE_URL,
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
    const payload = await readFilePreview(PUZZLE_DIRECTORY, req.params.name);
    res.json(payload);
  } catch (error) {
    res.status(400).json({ error: error.message });
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
