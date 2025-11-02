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

await fs.mkdir(WORKSPACE_ROOT, { recursive: true });

const app = express();
app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const ensureWorkspace = async (user) => {
  const safeUser = user?.replace(/[^a-zA-Z0-9_-]/g, '') || DEFAULT_USER;
  const dir = path.join(WORKSPACE_ROOT, safeUser);
  await fs.mkdir(dir, { recursive: true });
  return dir;
};

app.get('/health', (_req, res) => {
  res.json({ ok: true, workspaces: WORKSPACE_ROOT });
});

app.post('/save', async (req, res) => {
  try {
    const { user = DEFAULT_USER, filename = 'main.py', content = '' } = req.body || {};
    if (typeof filename !== 'string' || !filename.trim()) {
      return res.status(400).json({ ok: false, error: 'filename required' });
    }

    const dir = await ensureWorkspace(user);
    const filePath = path.join(dir, filename);
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, content, 'utf8');
    res.json({ ok: true, path: filePath });
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
  ws.on('message', async (raw) => {
    let payload;
    try {
      payload = JSON.parse(raw.toString());
    } catch (error) {
      ws.send(JSON.stringify({ type: 'error', data: 'invalid json payload' }));
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
      const containerName = `echo-run-${uuid()}`;
      const spawnArgs = dockerArgs.concat(['--name', containerName, cfg.image], entry);

      const docker = spawn('docker', spawnArgs, { env: process.env });

      const killContainer = () => {
        spawn('docker', ['kill', containerName]).on('error', (error) => {
          console.warn('failed to kill container', error.message);
        });
      };

      const cleanup = () => {
        clearTimeout(killTimer);
        ws.removeListener('close', onWsClose);
      };

      const onWsClose = () => {
        killContainer();
        cleanup();
      };

      const killTimer = setTimeout(() => {
        killContainer();
        cleanup();
      }, cfg.timeLimitMs);

      ws.once('close', onWsClose);

      docker.stdout.on('data', (chunk) => {
        ws.send(JSON.stringify({ type: 'stdout', data: chunk.toString() }));
      });

      docker.stderr.on('data', (chunk) => {
        ws.send(JSON.stringify({ type: 'stderr', data: chunk.toString() }));
      });

      docker.on('error', (error) => {
        ws.send(JSON.stringify({ type: 'error', data: `failed to spawn docker: ${error.message}` }));
        cleanup();
      });

      docker.on('close', (code) => {
        ws.send(JSON.stringify({ type: 'exit', code }));
        cleanup();
      });
    } catch (error) {
      console.error('run error', error);
      ws.send(JSON.stringify({ type: 'error', data: 'failed to launch run' }));
    }
  });
});

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

process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  server.close(() => process.exit(0));
});
