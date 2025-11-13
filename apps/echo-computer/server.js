import express from 'express';
import { WebSocketServer } from 'ws';
import { spawn } from 'node:child_process';
import { v4 as uuid } from 'uuid';
import path from 'node:path';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT || 8080);
const DEFAULT_USER = process.env.ECHO_USER || 'demo';
const WORKSPACE_ROOT = path.resolve(
  process.env.ECHO_WORKSPACE_ROOT || path.join(process.cwd(), 'workspaces')
);
const TASKS_FILE = path.join(__dirname, 'daily_tasks.json');

await fs.mkdir(WORKSPACE_ROOT, { recursive: true });

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

app.get('/health', (_req, res) => {
  res.json({ ok: true, workspaces: WORKSPACE_ROOT });
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
  return cachedDailyTasks;
}

process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  server.close(() => process.exit(0));
});
