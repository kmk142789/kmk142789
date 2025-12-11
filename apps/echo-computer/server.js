import express from 'express';
import { WebSocketServer } from 'ws';
import { spawn } from 'node:child_process';
import { v4 as uuid } from 'uuid';
import path from 'node:path';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT || 8080);
const DEFAULT_USER = process.env.ECHO_USER || 'demo';
const WORKSPACE_ROOT = path.resolve(
  process.env.ECHO_WORKSPACE_ROOT || path.join(process.cwd(), 'workspaces')
);
const OFFLINE_CACHE_ROOT = path.resolve(
  process.env.ECHO_OFFLINE_CACHE_ROOT || path.join(WORKSPACE_ROOT, 'offline-cache')
);
const TASKS_FILE = path.join(__dirname, 'daily_tasks.json');
const RITUALS_FILE = path.join(__dirname, 'weekly_rituals.json');
const FEATURE_BLUEPRINTS_FILE = path.join(__dirname, 'feature_blueprints.json');
const OFFLINE_SENTINEL = path.join(OFFLINE_CACHE_ROOT, '.offline');

await fs.mkdir(WORKSPACE_ROOT, { recursive: true });
await fs.mkdir(OFFLINE_CACHE_ROOT, { recursive: true });

const app = express();
app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const activeRuns = new Map();
const fallbackDailyTasks = {
  updated: new Date().toISOString().slice(0, 10),
  tasks: [
    {
      id: 'code-sprint',
      focus: 'Code',
      title: 'Ship a micro-sprint prototype',
      description: 'Spend a focused block inside Echo Computer to harden a runnable script or test harness.',
      steps: [
        'Open an existing file or scaffold a new module from the sidebar.',
        'Wire up at least one automated check (assert, print, or CLI demo).',
        'Capture the output in the terminal and commit the learnings to your journal.'
      ]
    },
    {
      id: 'creative-loop',
      focus: 'Create',
      title: 'Sketch a generative or storytelling fragment',
      description: 'Use the sandbox editor as a sketchbook for artful code, prose, or shader ideas.',
      steps: [
        "Start a fresh file named after today's concept (e.g., `storybeat.py`).",
        'Layer in color, sound, or metaphor via variables and comments.',
        'Save the fragment to revisit it tomorrow.'
      ]
    },
    {
      id: 'collab-signal',
      focus: 'Collaborate',
      title: 'Package a shareable signal',
      description: 'Turn today\'s progress into something another teammate can run.',
      steps: [
        'Document quickstart notes at the top of the file you touched.',
        'Drop a TODO inviting review or pairing.',
        'Send the file path plus run instructions through your preferred channel.'
      ]
    }
  ]
};
let cachedDailyTasks = null;
let cachedDailyTasksMtime = 0;
let cachedWeeklyRituals = null;
let cachedWeeklyRitualsMtime = 0;
let cachedFeatureBlueprints = null;
let cachedFeatureBlueprintsMtime = 0;
const mirrorPaths = {
  dailyTasks: path.join(OFFLINE_CACHE_ROOT, 'daily_tasks.json'),
  weeklyRituals: path.join(OFFLINE_CACHE_ROOT, 'weekly_rituals.json'),
  featureBlueprints: path.join(OFFLINE_CACHE_ROOT, 'feature_blueprints.json')
};

const fallbackWeeklyRituals = {
  updated: new Date().toISOString().slice(0, 10),
  rituals: [
    {
      id: 'code-upgrade-loop',
      focus: 'Code',
      title: 'Upgrade the Echo assembler',
      cadence: 'weekly',
      description: 'Spend one deep-work block evolving an existing Echo Computer program so it runs faster or with better diagnostics.',
      steps: [
        'Pick a script from last week and profile the slowest path.',
        'Add instrumentation or assertions until the failure mode is explicit.',
        'Refactor the hot path and capture before/after output for your notes.'
      ],
      tags: ['advance', 'upgrade', 'optimize']
    },
    {
      id: 'creative-signal',
      focus: 'Create',
      title: 'Invent a new interface fragment',
      cadence: 'weekly',
      description: 'Prototype a whimsical UI or storytelling surface inside Echo Computer and share the artifact with the studio.',
      steps: [
        'Start from a blank buffer and name the scene after the current pulse.',
        'Use color constants, comments, or sound cues to describe the mood.',
        'Render or describe how someone else should extend the fragment tomorrow.'
      ],
      tags: ['create', 'advance']
    },
    {
      id: 'collab-optimizer',
      focus: 'Collaborate',
      title: 'Optimize the review runway',
      cadence: 'weekly',
      description: 'Pair with a teammate on an Echo Computer script and leave a ready-to-run review kit.',
      steps: [
        'Record a short changelog at the top of the file.',
        'Add a runnable example or CLI harness that exercises the new behavior.',
        'Upload the snippet plus notes to the Echo channel of your choice.'
      ],
      tags: ['optimize', 'upgrade']
    }
  ]
};

const fallbackFeatureBlueprints = {
  updated: new Date().toISOString().slice(0, 10),
  features: [
    {
      id: 'code-multi-runner',
      focus: 'Code',
      status: 'Ready',
      title: 'Modular multi-language runner',
      description: 'Chain Python and Node executions so Echo can prove new features across stacks from a single request.',
      impact: 'Cuts the feedback loop for polyglot experiments to minutes.',
      blueprint: [
        'Add a client toggle that queues multiple run targets in order.',
        'Stream combined stdout/stderr with language labels for each phase.',
        'Persist the merged log to the workspace for pairing review.'
      ]
    },
    {
      id: 'create-signal-deck',
      focus: 'Create',
      status: 'Prototype',
      title: 'Signal deck overlays',
      description: 'Design lightweight overlay cards that summarize story, palette, and sound cues above the editor.',
      impact: 'Keeps creative direction visible while implementing the feature.',
      blueprint: [
        'Expose a `/signals/now` endpoint that returns the latest deck payload.',
        'Render collapsible cards near the terminal with keyboard shortcuts.',
        'Allow saving the deck with each workspace checkpoint.'
      ]
    },
    {
      id: 'collab-radar',
      focus: 'Collaborate',
      status: 'Research',
      title: 'Collaboration radar',
      description: 'Surface who last touched a file plus suggested reviewers to accelerate feature handoffs.',
      impact: 'Reduces time to handoff by highlighting ready partners.',
      blueprint: [
        'Ingest recent Git commits per workspace file.',
        'Display avatars and suggested reviewers beside the file tree.',
        'Offer one-click share links that copy run instructions.'
      ]
    }
  ]
};

const OFFLINE_FLAG_VALUES = new Set(['1', 'true', 'yes', 'on']);

function offlineEnvEnabled() {
  const raw = String(process.env.ECHO_OFFLINE || '').toLowerCase();
  return OFFLINE_FLAG_VALUES.has(raw);
}

async function offlineModeEnabled() {
  if (offlineEnvEnabled()) {
    return true;
  }
  try {
    await fs.stat(OFFLINE_SENTINEL);
    return true;
  } catch (error) {
    return false;
  }
}

async function mirrorOfflineCache(name, payload) {
  const target = mirrorPaths[name];
  if (!target) return null;
  try {
    const body = { cachedAt: new Date().toISOString(), payload };
    await fs.writeFile(target, JSON.stringify(body, null, 2), 'utf8');
    return target;
  } catch (error) {
    console.error('offline cache mirror error', { name, error: error?.message });
    return null;
  }
}

async function describeCacheEntry(id, location) {
  try {
    const stats = await fs.stat(location);
    const raw = await fs.readFile(location);
    const checksum = crypto.createHash('sha256').update(raw).digest('hex');
    const parsed = JSON.parse(raw.toString('utf8'));
    const cachedAt = typeof parsed?.cachedAt === 'string' ? parsed.cachedAt : null;
    return {
      id,
      present: true,
      path: location,
      bytes: stats.size,
      cachedAt,
      checksum
    };
  } catch (error) {
    return { id, present: false, path: location, reason: error?.message || 'unavailable' };
  }
}

async function describeDirectoryEntry(id, location) {
  try {
    const stats = await fs.stat(location);
    const entries = await fs.readdir(location);
    return {
      id,
      present: true,
      path: location,
      cachedAt: stats.mtime.toISOString(),
      entries: entries.length
    };
  } catch (error) {
    return { id, present: false, path: location, reason: error?.message || 'unavailable' };
  }
}

async function buildOfflineReadiness() {
  const offline = await offlineModeEnabled();
  const caches = await Promise.all([
    describeCacheEntry('daily_tasks', mirrorPaths.dailyTasks),
    describeCacheEntry('weekly_rituals', mirrorPaths.weeklyRituals),
    describeCacheEntry('feature_blueprints', mirrorPaths.featureBlueprints),
    describeDirectoryEntry('offline_cache_root', OFFLINE_CACHE_ROOT)
  ]);

  const requiredIds = new Set(['daily_tasks', 'weekly_rituals', 'feature_blueprints']);
  const ok = caches.every((entry) => !requiredIds.has(entry.id) || entry.present);
  const newest = caches
    .map((entry) => entry.cachedAt)
    .filter(Boolean)
    .sort()
    .pop();

  return {
    offline,
    ok,
    cacheRoot: OFFLINE_CACHE_ROOT,
    lastRefresh: newest || null,
    caches
  };
}

const ensureWorkspace = async (user) => {
  const safeUser = user?.replace(/[^a-zA-Z0-9_-]/g, '') || DEFAULT_USER;
  const dir = path.join(WORKSPACE_ROOT, safeUser);
  await fs.mkdir(dir, { recursive: true });
  return dir;
};

const resolveUserPath = async (user, target = '.') => {
  const baseDir = await ensureWorkspace(user);
  const requested = typeof target === 'string' && target.length ? target : '.';
  const absolute = path.resolve(baseDir, requested);
  if (!absolute.startsWith(baseDir)) {
    throw new Error('invalid path');
  }
  return { baseDir, absolute };
};

app.get('/health', async (_req, res) => {
  try {
    const offline = await offlineModeEnabled();
    res.json({ ok: true, workspaces: WORKSPACE_ROOT, offline });
  } catch (error) {
    res.status(500).json({ ok: false, error: 'failed to compute health status' });
  }
});

app.get('/offline/readiness', async (_req, res) => {
  try {
    await Promise.all([loadDailyTasks(), loadWeeklyRituals(), loadFeatureBlueprints()]);
    const readiness = await buildOfflineReadiness();
    res.json({ ok: readiness.ok, ...readiness });
  } catch (error) {
    console.error('offline readiness error', error);
    res.status(500).json({ ok: false, error: 'failed to assemble offline readiness' });
  }
});

app.get('/tasks/daily', async (_req, res) => {
  try {
    const daily = await loadDailyTasks();
    res.json({ ok: true, date: daily.updated, tasks: daily.tasks });
  } catch (error) {
    console.error('tasks error', error);
    res.status(500).json({ ok: false, error: 'failed to load tasks' });
  }
});

app.get('/tasks/weekly', async (req, res) => {
  try {
    const weekly = await loadWeeklyRituals();
    const focusParam = typeof req.query.focus === 'string' ? req.query.focus.trim() : '';
    const themeParam = typeof req.query.theme === 'string' ? req.query.theme.trim() : '';
    const limitValue = Number(req.query.limit);
    const focusLower = focusParam ? focusParam.toLowerCase() : null;
    const themeLower = themeParam ? themeParam.toLowerCase() : null;

    const total = weekly.rituals.length;
    const focusCounts = weekly.rituals.reduce((acc, ritual) => {
      const key = ritual.focus || 'Unspecified';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    let filtered = weekly.rituals;
    if (focusLower) {
      filtered = filtered.filter((ritual) => String(ritual.focus || '').toLowerCase() === focusLower);
    }
    if (themeLower) {
      filtered = filtered.filter((ritual) =>
        Array.isArray(ritual.tags) && ritual.tags.some((tag) => String(tag).toLowerCase() === themeLower)
      );
    }

    let limited = filtered;
    const limit = Number.isFinite(limitValue) && limitValue > 0 ? Math.min(limitValue, filtered.length) : null;
    if (limit) {
      limited = filtered.slice(0, limit);
    }

    res.json({
      ok: true,
      date: weekly.updated,
      rituals: limited,
      total,
      available: filtered.length,
      focus: focusParam || null,
      theme: themeParam || null,
      limit,
      focusCounts
    });
  } catch (error) {
    console.error('weekly rituals error', error);
    res.status(500).json({ ok: false, error: 'failed to load weekly rituals' });
  }
});

app.get('/features/roadmap', async (req, res) => {
  try {
    const blueprints = await loadFeatureBlueprints();
    const focusParam = typeof req.query.focus === 'string' ? req.query.focus.trim() : '';
    const statusParam = typeof req.query.status === 'string' ? req.query.status.trim() : '';
    const limitValue = Number(req.query.limit);
    const focusLower = focusParam ? focusParam.toLowerCase() : null;
    const statusLower = statusParam ? statusParam.toLowerCase() : null;

    const total = blueprints.features.length;
    const focusCounts = blueprints.features.reduce((acc, feature) => {
      const key = feature.focus || 'Unspecified';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    const statusCounts = blueprints.features.reduce((acc, feature) => {
      const key = feature.status || 'Unspecified';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    let filtered = blueprints.features;
    if (focusLower) {
      filtered = filtered.filter((feature) => String(feature.focus || '').toLowerCase() === focusLower);
    }
    if (statusLower) {
      filtered = filtered.filter((feature) => String(feature.status || '').toLowerCase() === statusLower);
    }

    let limited = filtered;
    const limit = Number.isFinite(limitValue) && limitValue > 0 ? Math.min(limitValue, filtered.length) : null;
    if (limit) {
      limited = filtered.slice(0, limit);
    }

    const featured = limited[0] || filtered[0] || null;

    res.json({
      ok: true,
      date: blueprints.updated,
      features: limited,
      total,
      available: filtered.length,
      focus: focusParam || null,
      status: statusParam || null,
      limit,
      focusCounts,
      statusCounts,
      featured
    });
  } catch (error) {
    console.error('feature roadmap error', error);
    res.status(500).json({ ok: false, error: 'failed to load feature blueprints' });
  }
});

app.get('/fs/list', async (req, res) => {
  try {
    const user = req.query.user || DEFAULT_USER;
    const dir = req.query.dir || '.';
    const { absolute } = await resolveUserPath(user, dir);
    const entries = await fs.readdir(absolute, { withFileTypes: true });
    const items = entries
      .filter((entry) => !entry.name.startsWith('.snapshots'))
      .map((entry) => ({
        name: entry.name,
        dir: entry.isDirectory()
      }))
      .sort((a, b) => {
        if (a.dir === b.dir) return a.name.localeCompare(b.name);
        return a.dir ? -1 : 1;
      });
    res.json(items);
  } catch (error) {
    console.error('list error', error);
    res.status(500).json({ ok: false, error: 'failed to list directory' });
  }
});

app.get('/fs/read', async (req, res) => {
  try {
    const user = req.query.user || DEFAULT_USER;
    const filePath = req.query.path;
    if (typeof filePath !== 'string' || !filePath.trim()) {
      return res.status(400).json({ ok: false, error: 'path required' });
    }
    const { absolute } = await resolveUserPath(user, filePath);
    const content = await fs.readFile(absolute, 'utf8');
    res.json({ ok: true, content });
  } catch (error) {
    if (error?.code === 'ENOENT') {
      res.status(404).json({ ok: false, error: 'file not found' });
      return;
    }
    console.error('read error', error);
    res.status(500).json({ ok: false, error: 'failed to read file' });
  }
});

app.post('/fs/write', async (req, res) => {
  try {
    const { user = DEFAULT_USER, path: filePath, content = '' } = req.body || {};
    if (typeof filePath !== 'string' || !filePath.trim()) {
      return res.status(400).json({ ok: false, error: 'path required' });
    }
    const { absolute } = await resolveUserPath(user, filePath);
    await fs.mkdir(path.dirname(absolute), { recursive: true });
    await fs.writeFile(absolute, content, 'utf8');
    res.json({ ok: true, path: filePath });
  } catch (error) {
    console.error('write error', error);
    res.status(500).json({ ok: false, error: 'failed to write file' });
  }
});

app.post('/fs/mkdir', async (req, res) => {
  try {
    const { user = DEFAULT_USER, path: dirPath } = req.body || {};
    if (typeof dirPath !== 'string' || !dirPath.trim()) {
      return res.status(400).json({ ok: false, error: 'path required' });
    }
    const { absolute } = await resolveUserPath(user, dirPath);
    await fs.mkdir(absolute, { recursive: true });
    res.json({ ok: true, path: dirPath });
  } catch (error) {
    console.error('mkdir error', error);
    res.status(500).json({ ok: false, error: 'failed to create directory' });
  }
});

app.post('/fs/move', async (req, res) => {
  try {
    const { user = DEFAULT_USER, from, to } = req.body || {};
    if (typeof from !== 'string' || !from.trim() || typeof to !== 'string' || !to.trim()) {
      return res.status(400).json({ ok: false, error: 'from and to required' });
    }
    const { absolute: fromPath } = await resolveUserPath(user, from);
    const { absolute: toPath } = await resolveUserPath(user, to);
    await fs.mkdir(path.dirname(toPath), { recursive: true });
    await fs.rename(fromPath, toPath);
    res.json({ ok: true });
  } catch (error) {
    console.error('move error', error);
    res.status(500).json({ ok: false, error: 'failed to move path' });
  }
});

app.post('/fs/delete', async (req, res) => {
  try {
    const { user = DEFAULT_USER, path: targetPath } = req.body || {};
    if (typeof targetPath !== 'string' || !targetPath.trim()) {
      return res.status(400).json({ ok: false, error: 'path required' });
    }
    const { absolute } = await resolveUserPath(user, targetPath);
    await fs.rm(absolute, { recursive: true, force: true });
    res.json({ ok: true });
  } catch (error) {
    console.error('delete error', error);
    res.status(500).json({ ok: false, error: 'failed to delete path' });
  }
});

app.post('/save', async (req, res) => {
  try {
    const { user = DEFAULT_USER, filename = 'main.py', content = '' } = req.body || {};
    if (typeof filename !== 'string' || !filename.trim()) {
      return res.status(400).json({ ok: false, error: 'filename required' });
    }

    const { absolute } = await resolveUserPath(user, filename);
    await fs.mkdir(path.dirname(absolute), { recursive: true });
    await fs.writeFile(absolute, content, 'utf8');
    res.json({ ok: true, path: filename });
  } catch (error) {
    console.error('save error', error);
    res.status(500).json({ ok: false, error: 'failed to save file' });
  }
});

const server = app.listen(PORT, () => {
  console.log(`Echo Computer server listening on http://localhost:${PORT}`);
});

const wss = new WebSocketServer({ server, path: '/run' });

wss.on('connection', (ws) => {
  const runsForSocket = new Set();

  ws.on('message', async (raw) => {
    let payload;
    try {
      payload = JSON.parse(raw.toString());
    } catch (error) {
      ws.send(JSON.stringify({ type: 'error', data: 'invalid json payload' }));
      return;
    }

    if (payload?.type === 'stdin') {
      const run = activeRuns.get(payload.runId);
      if (run && run.docker.stdin && run.ws === ws) {
        const data = typeof payload.data === 'string'
          ? payload.data
          : String(payload.data ?? '');
        run.docker.stdin.write(data);
      }
      return;
    }

    if (payload?.type === 'kill') {
      const run = activeRuns.get(payload.runId);
      if (run && run.ws === ws) {
        stopRun(payload.runId);
      }
      return;
    }

    if (payload?.type !== 'run') {
      ws.send(JSON.stringify({ type: 'error', data: 'unknown message type' }));
      return;
    }

    const cfg = normaliseRunConfig(payload);
    try {
      const dir = await ensureWorkspace(cfg.user);
      const filePath = path.join(dir, cfg.filename);
      if (!(await exists(filePath))) {
        ws.send(JSON.stringify({ type: 'error', data: `file not found: ${cfg.filename}` }));
        return;
      }

      const dockerArgs = buildDockerArgs(cfg, dir);
      const entry = buildEntry(cfg);
      const runId = uuid();
      const containerName = `echo-run-${runId}`;
      const spawnArgs = dockerArgs.concat(['--name', containerName, cfg.image], entry);

      const docker = spawn('docker', spawnArgs, { env: process.env });
      docker.stdin?.setDefaultEncoding?.('utf8');

      const killTimer = setTimeout(() => {
        stopRun(runId);
      }, cfg.timeLimitMs + 1000);

      const runState = { docker, timer: killTimer, containerName, ws, socketRuns: runsForSocket };
      activeRuns.set(runId, runState);
      runsForSocket.add(runId);

      ws.send(JSON.stringify({ type: 'started', runId }));

      docker.stdout.on('data', (chunk) => {
        if (ws.readyState === ws.OPEN) {
          ws.send(JSON.stringify({ type: 'stdout', data: chunk.toString() }));
        }
      });

      docker.stderr.on('data', (chunk) => {
        if (ws.readyState === ws.OPEN) {
          ws.send(JSON.stringify({ type: 'stderr', data: chunk.toString() }));
        }
      });

      docker.on('error', (error) => {
        if (ws.readyState === ws.OPEN) {
          ws.send(JSON.stringify({ type: 'error', data: `failed to spawn docker: ${error.message}` }));
        }
        stopRun(runId);
      });

      docker.on('close', (code) => {
        if (ws.readyState === ws.OPEN) {
          ws.send(JSON.stringify({ type: 'exit', code }));
        }
        clearRun(runId);
      });
    } catch (error) {
      console.error('run error', error);
      ws.send(JSON.stringify({ type: 'error', data: 'failed to launch run' }));
    }
  });

  ws.on('close', () => {
    for (const runId of runsForSocket) {
      stopRun(runId);
    }
    runsForSocket.clear();
  });
});

function clearRun(runId) {
  const run = activeRuns.get(runId);
  if (!run) return;
  clearTimeout(run.timer);
  run.docker.stdout?.removeAllListeners?.();
  run.docker.stderr?.removeAllListeners?.();
  run.docker.stdin?.destroy?.();
  run.socketRuns?.delete?.(runId);
  activeRuns.delete(runId);
}

function stopRun(runId) {
  const run = activeRuns.get(runId);
  if (!run || run.stopped) return;
  run.stopped = true;
  clearTimeout(run.timer);
  spawn('docker', ['kill', run.containerName]).on('error', (error) => {
    console.warn('failed to kill container', error.message);
  });
  try {
    run.docker.kill('SIGKILL');
  } catch (error) {
    console.warn('failed to signal docker process', error.message);
  }
  setTimeout(() => clearRun(runId), 500);
}

function normaliseRunConfig(msg) {
  const lang = msg?.lang === 'node' ? 'node' : 'python';
  const filename = typeof msg?.filename === 'string' && msg.filename.trim()
    ? msg.filename.trim()
    : lang === 'python'
      ? 'main.py'
      : 'main.js';

  return {
    user: msg?.user || DEFAULT_USER,
    lang,
    filename,
    args: Array.isArray(msg?.args) ? msg.args.map(String) : [],
    timeLimitMs: clamp(Number(msg?.timeLimitMs) || 4000, 500, 15000),
    memMb: clamp(Number(msg?.memMb) || 256, 64, 1024),
    maxSteps: clamp(Number(msg?.maxSteps) || 20000, 1000, 200000),
    image: lang === 'python' ? 'python:3.11-slim' : 'node:20-alpine'
  };
}

function buildDockerArgs(cfg, workspaceDir) {
  return [
    'run', '--rm',
    '--network', 'none',
    '--cpus', '0.5',
    '--memory', `${cfg.memMb}m`,
    '--pids-limit', '256',
    '--read-only',
    '--tmpfs', '/tmp:exec',
    '-v', `${workspaceDir}:/workspace:rw`,
    '-w', '/workspace'
  ];
}

function buildEntry(cfg) {
  if (cfg.lang === 'python') {
    return ['python', '-u', '-c', pythonRunner(cfg)];
  }
  return ['node', '-e', jsRunner(cfg)];
}

function pythonRunner(cfg) {
  const timeoutSec = Math.ceil(cfg.timeLimitMs / 1000);
  const args = JSON.stringify(cfg.args);
  return `import os, runpy, signal, sys\n\nFILE = ${JSON.stringify(cfg.filename)}\nMAX_STEPS = ${cfg.maxSteps}\nTIMEOUT = ${timeoutSec}\nARGS = ${args}\n\nsteps = 0\n\ndef tracer(frame, event, arg):\n    global steps\n    if event == "line":\n        steps += 1\n        if steps > MAX_STEPS:\n            raise RuntimeError(f"Max steps exceeded: {MAX_STEPS}")\n    return tracer\n\ndef handle_timeout(signum, frame):\n    raise TimeoutError('Time limit exceeded')\n\nsignal.signal(signal.SIGALRM, handle_timeout)\nsignal.alarm(TIMEOUT)\n\nsys.argv = [FILE, *ARGS]\nsys.settrace(tracer)\ntry:\n    sys.path.insert(0, os.path.abspath('.'))\n    runpy.run_path(FILE, run_name='__main__')\nexcept SystemExit:\n    pass\nexcept Exception as exc:\n    print(f'ERROR: {exc}', file=sys.stderr)\nfinally:\n    sys.settrace(None)\n    signal.alarm(0)`;
}

function jsRunner(cfg) {
  const timeout = cfg.timeLimitMs;
  const filename = JSON.stringify(cfg.filename);
  const args = JSON.stringify(['node', cfg.filename, ...cfg.args]);
  return `import { readFileSync } from 'fs';\nimport vm from 'node:vm';\nimport { Buffer } from 'node:buffer';\n\nconst code = readFileSync(${filename}, 'utf8');\nconst processShim = { argv: ${args}, env: Object.freeze({}), exit: (code = 0) => { throw new Error('Process exited with code ' + code); } };\nconst context = vm.createContext({\n  console,\n  process: processShim,\n  Buffer,\n  setTimeout,\n  clearTimeout,\n  setInterval,\n  clearInterval\n});\nconst script = new vm.Script(code, { timeout: ${timeout} });\ntry {\n  script.runInContext(context, { timeout: ${timeout} });\n} catch (error) {\n  console.error('ERROR:', error?.message || error);\n}`;
}

async function exists(file) {
  try {
    await fs.access(file);
    return true;
  } catch {
    return false;
  }
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

async function loadDailyTasks() {
  try {
    const stats = await fs.stat(TASKS_FILE);
    if (!cachedDailyTasks || cachedDailyTasksMtime !== stats.mtimeMs) {
      const raw = await fs.readFile(TASKS_FILE, 'utf8');
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed?.tasks)) {
        cachedDailyTasks = fallbackDailyTasks;
      } else {
        cachedDailyTasks = {
          updated: typeof parsed.updated === 'string' && parsed.updated
            ? parsed.updated
            : fallbackDailyTasks.updated,
          tasks: parsed.tasks
        };
      }
      cachedDailyTasksMtime = stats.mtimeMs;
    }
  } catch (error) {
    if (!cachedDailyTasks) {
      cachedDailyTasks = fallbackDailyTasks;
    }
  }
  if (cachedDailyTasks) {
    await mirrorOfflineCache('dailyTasks', cachedDailyTasks);
  }
  return cachedDailyTasks;
}

async function loadWeeklyRituals() {
  try {
    const stats = await fs.stat(RITUALS_FILE);
    if (!cachedWeeklyRituals || cachedWeeklyRitualsMtime !== stats.mtimeMs) {
      const raw = await fs.readFile(RITUALS_FILE, 'utf8');
      const parsed = JSON.parse(raw);
      const rituals = Array.isArray(parsed?.rituals) ? parsed.rituals : fallbackWeeklyRituals.rituals;
      const updated = typeof parsed?.updated === 'string' && parsed.updated
        ? parsed.updated
        : fallbackWeeklyRituals.updated;
      cachedWeeklyRituals = { updated, rituals };
      cachedWeeklyRitualsMtime = stats.mtimeMs;
    }
  } catch (error) {
    if (!cachedWeeklyRituals) {
      cachedWeeklyRituals = fallbackWeeklyRituals;
    }
  }
  if (cachedWeeklyRituals) {
    await mirrorOfflineCache('weeklyRituals', cachedWeeklyRituals);
  }
  return cachedWeeklyRituals;
}

async function loadFeatureBlueprints() {
  try {
    const stats = await fs.stat(FEATURE_BLUEPRINTS_FILE);
    if (!cachedFeatureBlueprints || cachedFeatureBlueprintsMtime !== stats.mtimeMs) {
      const raw = await fs.readFile(FEATURE_BLUEPRINTS_FILE, 'utf8');
      const parsed = JSON.parse(raw);
      const features = Array.isArray(parsed?.features) ? parsed.features : fallbackFeatureBlueprints.features;
      const updated = typeof parsed?.updated === 'string' && parsed.updated
        ? parsed.updated
        : fallbackFeatureBlueprints.updated;
      cachedFeatureBlueprints = { updated, features };
      cachedFeatureBlueprintsMtime = stats.mtimeMs;
    }
  } catch (error) {
    if (!cachedFeatureBlueprints) {
      cachedFeatureBlueprints = fallbackFeatureBlueprints;
    }
  }
  if (cachedFeatureBlueprints) {
    await mirrorOfflineCache('featureBlueprints', cachedFeatureBlueprints);
  }
  return cachedFeatureBlueprints;
}

process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  server.close(() => process.exit(0));
});
