import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

type GitStatus = 'clean' | 'modified' | 'staged' | 'behind' | 'ahead' | 'syncing';

type GitRepo = {
  name: string;
  branch: string;
  commits: number;
  status: GitStatus;
  lastCommitTs: number;
  activity: number;
  blockers: number;
};

type SystemStats = {
  cpu: number;
  memory: number;
  networkIn: number;
  networkOut: number;
  temperature: number;
};

type TerminalSession = {
  id: string;
  path: string;
  history: string[];
};

type FileEntry =
  | {
      type: 'dir';
    }
  | {
      type: 'file';
      content: string;
    };

type FileSystemState = Record<string, FileEntry>;

type AiLogLevel = 'info' | 'success' | 'warning';

type AiLogEntry = {
  message: string;
  type: AiLogLevel;
  timestamp: string;
};

type AiTaskStatus = 'queued' | 'running' | 'complete';

type AiTask = {
  id: string;
  description: string;
  status: AiTaskStatus;
  createdAt: number;
};

type CommandResult = {
  output: string[];
  newPath: string;
  fileSystem: FileSystemState;
};

const HOME_PATH = '/home/echo';

const BOOT_SEQUENCE = [
  'BIOS POST... OK',
  'Loading bootloader...',
  'EchoOS Kernel v4.0.0 loading...',
  'Initializing hardware...',
  '[OK] CPU detected: 8 cores @ 3.6GHz',
  '[OK] RAM: 16GB available',
  '[OK] Storage: 512GB SSD',
  'Starting system services...',
  '[OK] Network stack',
  '[OK] File system',
  '[OK] Process scheduler',
  '[OK] AI subsystem',
  '[OK] Container runtime',
  '[OK] Database engine',
  '',
  'EchoOS v4.0 ready.',
  'Welcome, Echo.'
];

const HELP_LINES = [
  'EchoOS Command Reference',
  '',
  'FILE SYSTEM',
  '  ls [path]        List directory contents',
  '  cd [path]        Change directory (default: home)',
  '  pwd              Print working directory',
  '  cat <file>       Display file contents',
  '  mkdir <dir>      Create directory',
  '  touch <file>     Create empty file',
  '  rm <path>        Remove file or directory',
  '  find <pattern>   Search for files containing pattern',
  '',
  'SYSTEM',
  '  help             Show this reference',
  '  clear            Clear terminal output',
  '',
  'AI',
  '  ai status        Inspect AI subsystem state',
  '  ai activate      Engage the AI co-pilot',
  '  ai deactivate    Suspend the AI co-pilot',
  '  ai task <text>   Queue a new AI mission',
  '  ai analyze       Summarise current signals',
  '  ai optimize      Tune telemetry for stability'
];

const INITIAL_FILE_SYSTEM: FileSystemState = {
  '/': { type: 'dir' },
  '/home': { type: 'dir' },
  [HOME_PATH]: { type: 'dir' },
  [`${HOME_PATH}/README.md`]: {
    type: 'file',
    content: '# EchoOS Control Center\nStay curious. Every command is logged for future constellations.'
  },
  [`${HOME_PATH}/notes.txt`]: {
    type: 'file',
    content: 'Pending: link ai optimizer with telemetry smoothing.'
  },
  '/var': { type: 'dir' },
  '/var/system.log': {
    type: 'file',
    content: '[boot] Kernel stabilised\n[network] Telemetry stream aligned'
  },
  '/etc': { type: 'dir' },
  '/etc/echo.conf': {
    type: 'file',
    content: 'mode=guardian\nai=enabled\nautonomy=regulated'
  },
  '/srv': { type: 'dir' },
  '/srv/pulses': { type: 'dir' },
  '/srv/pulses/cycle-142.json': {
    type: 'file',
    content: '{"joy":0.94,"nodes":18,"status":"radiant"}'
  }
};

const INITIAL_TERMINALS: Record<string, TerminalSession> = {
  'term-0': {
    id: 'term-0',
    path: '/',
    history: []
  }
};

const INITIAL_GIT_REPOS: GitRepo[] = [
  {
    name: 'ai-agent-core',
    branch: 'main',
    commits: 142,
    status: 'clean',
    lastCommitTs: Date.now() - 1000 * 60 * 60 * 2,
    activity: 0.86,
    blockers: 0
  },
  {
    name: 'web-scraper',
    branch: 'develop',
    commits: 67,
    status: 'modified',
    lastCommitTs: Date.now() - 1000 * 60 * 15,
    activity: 0.72,
    blockers: 2
  },
  {
    name: 'ml-pipeline',
    branch: 'feature/training',
    commits: 89,
    status: 'staged',
    lastCommitTs: Date.now() - 1000 * 60 * 45,
    activity: 0.79,
    blockers: 1
  }
];

const clamp = (value: number, min: number, max: number): number => Math.min(Math.max(value, min), max);

const normalizePath = (input: string): string => {
  if (!input || input === '/') {
    return '/';
  }
  const segments = input.split('/').filter(Boolean);
  const stack: string[] = [];
  segments.forEach((segment) => {
    if (segment === '.' || segment === '') {
      return;
    }
    if (segment === '..') {
      stack.pop();
      return;
    }
    stack.push(segment);
  });
  return `/${stack.join('/')}` || '/';
};

const resolvePath = (cwd: string, target?: string): string => {
  if (!target || target === '.') {
    return cwd;
  }
  if (target === '~') {
    return HOME_PATH;
  }
  if (target.startsWith('/')) {
    return normalizePath(target);
  }
  return normalizePath(`${cwd}/${target}`);
};

const parentPath = (path: string): string => {
  if (path === '/' || path === '') {
    return '/';
  }
  const segments = path.split('/').filter(Boolean);
  segments.pop();
  return segments.length ? `/${segments.join('/')}` : '/';
};

const basename = (path: string): string => {
  if (path === '/' || path === '') {
    return '/';
  }
  const segments = path.split('/').filter(Boolean);
  return segments[segments.length - 1] ?? '/';
};

const listDirectory = (fs: FileSystemState, path: string): { name: string; entry: FileEntry }[] => {
  const entries: { name: string; entry: FileEntry }[] = [];
  Object.entries(fs).forEach(([entryPath, entry]) => {
    if (entryPath === path) {
      return;
    }
    if (parentPath(entryPath) === path) {
      entries.push({ name: basename(entryPath), entry });
    }
  });
  return entries.sort((a, b) => {
    if (a.entry.type === b.entry.type) {
      return a.name.localeCompare(b.name);
    }
    return a.entry.type === 'dir' ? -1 : 1;
  });
};

const removeEntry = (fs: FileSystemState, target: string): FileSystemState => {
  const filtered = Object.fromEntries(
    Object.entries(fs).filter(([path]) => path !== target && !path.startsWith(`${target}/`))
  );
  return Object.keys(filtered).length ? filtered : { '/': { type: 'dir' } };
};

const formatListEntry = (name: string, entry: FileEntry): string => {
  if (entry.type === 'dir') {
    return `drwxr-xr-x      -  ${name}/`;
  }
  const size = entry.content.length;
  return `-rw-r--r--  ${String(size).padStart(6, ' ')}B  ${name}`;
};

const formatRelativeTime = (timestamp: number): string => {
  const delta = Date.now() - timestamp;
  const seconds = Math.max(1, Math.round(delta / 1000));
  if (seconds < 60) {
    return `${seconds}s ago`;
  }
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.round(hours / 24);
  return `${days}d ago`;
};

const uniqueId = (): string => Math.random().toString(36).slice(2, 8);

const runCommand = (
  input: string,
  session: TerminalSession,
  fs: FileSystemState
): CommandResult => {
  const trimmed = input.trim();
  if (!trimmed) {
    return { output: [], newPath: session.path, fileSystem: fs };
  }

  const [command, ...rest] = trimmed.split(/\s+/);
  let nextFs = fs;
  let newPath = session.path;
  const output: string[] = [];

  switch (command) {
    case 'help': {
      output.push(...HELP_LINES);
      break;
    }
    case 'pwd': {
      output.push(session.path);
      break;
    }
    case 'ls': {
      const target = resolvePath(session.path, rest[0]);
      const entry = fs[target];
      if (!entry) {
        output.push(`ls: cannot access '${target}': No such file or directory`);
        break;
      }
      if (entry.type === 'file') {
        output.push(formatListEntry(basename(target), entry));
        break;
      }
      const listing = listDirectory(fs, target);
      if (!listing.length) {
        output.push('(empty)');
      } else {
        listing.forEach((item) => {
          output.push(formatListEntry(item.name, item.entry));
        });
      }
      break;
    }
    case 'cd': {
      const target = resolvePath(session.path, rest[0] ?? HOME_PATH);
      const entry = fs[target];
      if (!entry) {
        output.push(`cd: no such file or directory: ${target}`);
        break;
      }
      if (entry.type !== 'dir') {
        output.push(`cd: not a directory: ${target}`);
        break;
      }
      newPath = target;
      break;
    }
    case 'cat': {
      if (!rest.length) {
        output.push('cat: missing file operand');
        break;
      }
      const target = resolvePath(session.path, rest[0]);
      const entry = fs[target];
      if (!entry) {
        output.push(`cat: ${target}: No such file`);
        break;
      }
      if (entry.type !== 'file') {
        output.push(`cat: ${target}: Is a directory`);
        break;
      }
      output.push(entry.content);
      break;
    }
    case 'mkdir': {
      if (!rest.length) {
        output.push('mkdir: missing operand');
        break;
      }
      const target = resolvePath(session.path, rest[0]);
      if (fs[target]) {
        output.push(`mkdir: cannot create directory '${target}': File exists`);
        break;
      }
      const parent = parentPath(target);
      const parentEntry = fs[parent];
      if (!parentEntry || parentEntry.type !== 'dir') {
        output.push(`mkdir: cannot create directory '${target}': Parent missing`);
        break;
      }
      nextFs = { ...fs, [target]: { type: 'dir' } };
      break;
    }
    case 'touch': {
      if (!rest.length) {
        output.push('touch: missing file operand');
        break;
      }
      const target = resolvePath(session.path, rest[0]);
      const parent = parentPath(target);
      const parentEntry = fs[parent];
      if (!parentEntry || parentEntry.type !== 'dir') {
        output.push(`touch: cannot create file '${target}': Parent missing`);
        break;
      }
      nextFs = {
        ...fs,
        [target]: {
          type: 'file',
          content: `// created ${new Date().toLocaleString()}`
        }
      };
      break;
    }
    case 'rm': {
      if (!rest.length) {
        output.push('rm: missing operand');
        break;
      }
      const target = resolvePath(session.path, rest[0]);
      if (target === '/') {
        output.push('rm: refusing to remove root directory');
        break;
      }
      if (!fs[target]) {
        output.push(`rm: cannot remove '${target}': No such file or directory`);
        break;
      }
      nextFs = removeEntry(fs, target);
      break;
    }
    case 'find': {
      if (!rest.length) {
        output.push('find: missing search pattern');
        break;
      }
      const pattern = rest[0].toLowerCase();
      const matches = Object.keys(fs).filter((path) => path.toLowerCase().includes(pattern));
      if (!matches.length) {
        output.push(`find: no entries match '${pattern}'`);
      } else {
        matches.sort().forEach((match) => output.push(match));
      }
      break;
    }
    default: {
      output.push(`Command not recognised: ${command}`);
      break;
    }
  }

  return { output, newPath, fileSystem: nextFs };
};

const statusStyles: Record<GitStatus, { background: string; border: string; color: string }> = {
  clean: {
    background: 'rgba(34,197,94,0.18)',
    border: 'rgba(34,197,94,0.45)',
    color: '#bbf7d0'
  },
  modified: {
    background: 'rgba(251,191,36,0.18)',
    border: 'rgba(251,191,36,0.45)',
    color: '#fef3c7'
  },
  staged: {
    background: 'rgba(14,165,233,0.18)',
    border: 'rgba(14,165,233,0.45)',
    color: '#bae6fd'
  },
  behind: {
    background: 'rgba(244,63,94,0.2)',
    border: 'rgba(244,63,94,0.5)',
    color: '#fecdd3'
  },
  ahead: {
    background: 'rgba(129,140,248,0.2)',
    border: 'rgba(129,140,248,0.5)',
    color: '#e0e7ff'
  },
  syncing: {
    background: 'rgba(59,130,246,0.18)',
    border: 'rgba(59,130,246,0.45)',
    color: '#dbeafe'
  }
};

const AiStatusPill: React.FC<{ active: boolean }> = ({ active }) => (
  <span className={`ecc-pill ${active ? 'ecc-pill--active' : 'ecc-pill--idle'}`}>
    {active ? 'ACTIVE' : 'STANDBY'}
  </span>
);

const TaskPill: React.FC<{ status: AiTaskStatus }> = ({ status }) => (
  <span className={`ecc-pill ecc-pill--${status}`}>
    {status.toUpperCase()}
  </span>
);

const StatBar: React.FC<{ label: string; value: number; max?: number }> = ({ label, value, max = 100 }) => (
  <div className="ecc-stat">
    <div className="ecc-stat__header">
      <span>{label}</span>
      <strong>{value.toFixed(1)}%</strong>
    </div>
    <div className="ecc-stat__bar">
      <div className="ecc-stat__bar-fill" style={{ width: `${clamp((value / max) * 100, 0, 100)}%` }} />
    </div>
  </div>
);

const statusMessage = (status: GitStatus): string => {
  switch (status) {
    case 'clean':
      return 'Synchronized with origin';
    case 'modified':
      return 'Local changes pending review';
    case 'staged':
      return 'Commits staged for merge';
    case 'behind':
      return 'Behind remote. Pull recommended';
    case 'ahead':
      return 'Ahead of remote. Ready to push';
    case 'syncing':
      return 'Rebasing and syncing commits';
    default:
      return 'Status unknown';
  }
};

const summarizeTasks = (tasks: AiTask[]): string => {
  if (!tasks.length) {
    return 'No queued missions';
  }
  const running = tasks.filter((task) => task.status === 'running').length;
  const queued = tasks.filter((task) => task.status === 'queued').length;
  const complete = tasks.filter((task) => task.status === 'complete').length;
  return `${running} running • ${queued} queued • ${complete} complete`;
};

const buildSnapshot = (repos: GitRepo[]) => {
  const total = repos.length;
  const modified = repos.filter((repo) => repo.status === 'modified').length;
  const staged = repos.filter((repo) => repo.status === 'staged').length;
  const behind = repos.filter((repo) => repo.status === 'behind').length;
  const averageActivity = total
    ? repos.reduce((sum, repo) => sum + repo.activity, 0) / total
    : 0;
  return {
    total,
    modified,
    staged,
    behind,
    averageActivity: averageActivity * 100
  };
};

const executeCode = (code: string, language: 'javascript' | 'python'): string => {
  try {
    const logs: string[] = [];
    const customConsole = {
      log: (...args: unknown[]) => logs.push(args.map(String).join(' ')),
      error: (...args: unknown[]) => logs.push(`ERROR: ${args.map(String).join(' ')}`),
      warn: (...args: unknown[]) => logs.push(`WARN: ${args.map(String).join(' ')}`)
    };

    if (language === 'javascript') {
      const fn = new Function('console', code);
      fn(customConsole);
    } else {
      logs.push('[Python 3.11.5 interpreter]');
      const lines = code.split('\n').map((line) => line.trim());
      lines.forEach((line) => {
        if (line.startsWith('print(') && line.endsWith(')')) {
          const inner = line.slice(6, -1).trim().replace(/^['\"]|['\"]$/g, '');
          logs.push(inner);
        }
      });
    }

    return logs.length ? logs.join('\n') : 'Process exited with code 0';
  } catch (error) {
    return `Execution error: ${(error as Error).message}`;
  }
};

const EchoControlCenter: React.FC = () => {
  const [gitRepos, setGitRepos] = useState<GitRepo[]>(INITIAL_GIT_REPOS);
  const [systemStats, setSystemStats] = useState<SystemStats>({
    cpu: 28,
    memory: 61,
    networkIn: 8.2,
    networkOut: 5.7,
    temperature: 58
  });
  const [terminalSessions, setTerminalSessions] = useState<Record<string, TerminalSession>>(INITIAL_TERMINALS);
  const [fileSystem, setFileSystem] = useState<FileSystemState>(INITIAL_FILE_SYSTEM);
  const [commandInput, setCommandInput] = useState('');
  const [bootStage, setBootStage] = useState(0);
  const [isBooted, setIsBooted] = useState(false);
  const [codeInput, setCodeInput] = useState("console.log('EchoOS ready');");
  const [codeLanguage, setCodeLanguage] = useState<'javascript' | 'python'>('javascript');
  const [codeOutput, setCodeOutput] = useState('');
  const [browserUrl, setBrowserUrl] = useState('https://echo.constellation.local');
  const [browserHistory, setBrowserHistory] = useState<{ url: string; timestamp: number }[]>([]);
  const [aiActive, setAiActive] = useState(false);
  const [aiLog, setAiLog] = useState<AiLogEntry[]>([]);
  const [aiTasks, setAiTasks] = useState<AiTask[]>([]);

  const terminalRef = useRef<HTMLDivElement | null>(null);
  const previousTasks = useRef<AiTask[]>([]);

  const addAiLog = useCallback((message: string, type: AiLogLevel = 'info') => {
    setAiLog((prev) => [{ message, type, timestamp: new Date().toLocaleTimeString() }, ...prev].slice(0, 40));
  }, []);

  useEffect(() => {
    addAiLog('Initializing EchoOS control center', 'info');
  }, [addAiLog]);

  useEffect(() => {
    if (bootStage >= BOOT_SEQUENCE.length) {
      if (!isBooted) {
        setTimeout(() => setIsBooted(true), 480);
      }
      return;
    }
    const delay = bootStage === 0 ? 520 : 180;
    const timer = window.setTimeout(() => {
      const line = BOOT_SEQUENCE[bootStage];
      setTerminalSessions((prev) => {
        const session = prev['term-0'];
        if (!session) {
          return prev;
        }
        const history = line === undefined ? session.history : [...session.history, line];
        return {
          ...prev,
          'term-0': {
            ...session,
            history
          }
        };
      });
      setBootStage((stage) => stage + 1);
    }, delay);
    return () => window.clearTimeout(timer);
  }, [bootStage, isBooted]);

  useEffect(() => {
    if (!isBooted) {
      return;
    }
    addAiLog('EchoOS handshake complete. Control center online.', 'success');
  }, [isBooted, addAiLog]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setSystemStats((prev) => ({
        cpu: clamp(prev.cpu + (Math.random() - 0.5) * 8, 5, 96),
        memory: clamp(prev.memory + (Math.random() - 0.5) * 4, 12, 95),
        networkIn: clamp(prev.networkIn + (Math.random() - 0.5) * 3, 0, 64),
        networkOut: clamp(prev.networkOut + (Math.random() - 0.5) * 2.5, 0, 48),
        temperature: clamp(prev.temperature + (Math.random() - 0.5) * 2.6, 45, 84)
      }));
    }, 2200);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setGitRepos((prev) =>
        prev.map((repo) => {
          let status = repo.status;
          let commits = repo.commits;
          let blockers = repo.blockers;
          let lastCommitTs = repo.lastCommitTs;
          const activity = clamp(repo.activity + (Math.random() - 0.5) * 0.12, 0.2, 0.98);

          const roll = Math.random();
          if (roll > 0.78) {
            commits += 1;
            status = 'clean';
            blockers = Math.max(0, blockers - 1);
            lastCommitTs = Date.now();
          } else if (roll > 0.6) {
            status = 'modified';
            blockers = Math.min(4, blockers + 1);
          } else if (roll < 0.12) {
            status = 'behind';
          } else if (roll < 0.24) {
            status = 'ahead';
          } else if (roll > 0.4 && roll < 0.5) {
            status = 'syncing';
          }

          return {
            ...repo,
            status,
            commits,
            blockers,
            activity,
            lastCommitTs
          };
        })
      );
    }, 9000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!aiActive) {
      return;
    }
    const timer = window.setInterval(() => {
      setAiTasks((prev) =>
        prev.map((task) => {
          if (task.status === 'queued') {
            return { ...task, status: 'running' };
          }
          if (task.status === 'running' && Math.random() > 0.45) {
            return { ...task, status: 'complete' };
          }
          return task;
        })
      );
    }, 5000);
    return () => window.clearInterval(timer);
  }, [aiActive]);

  useEffect(() => {
    const previous = previousTasks.current;
    aiTasks.forEach((task) => {
      const before = previous.find((entry) => entry.id === task.id);
      if (task.status === 'complete' && before?.status !== 'complete') {
        addAiLog(`AI mission resolved: ${task.description}`, 'success');
      }
    });
    previousTasks.current = aiTasks;
  }, [aiTasks, addAiLog]);

  useEffect(() => {
    const session = terminalSessions['term-0'];
    if (!session) {
      return;
    }
    const node = terminalRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = node.scrollHeight;
  }, [terminalSessions]);

  const snapshot = useMemo(() => buildSnapshot(gitRepos), [gitRepos]);

  const handleAiCommand = useCallback(
    (input: string): string[] => {
      const [, action, ...rest] = input.trim().split(/\s+/);
      const payload = rest.join(' ').trim();
      switch (action) {
        case 'status': {
          const summary = summarizeTasks(aiTasks);
          return [`AI status: ${aiActive ? 'ACTIVE' : 'STANDBY'}`, summary];
        }
        case 'activate': {
          if (aiActive) {
            return ['AI subsystem already engaged'];
          }
          setAiActive(true);
          addAiLog('AI co-pilot engaged. Monitoring signals.', 'success');
          return ['AI subsystem engaged'];
        }
        case 'deactivate': {
          if (!aiActive) {
            return ['AI subsystem already idle'];
          }
          setAiActive(false);
          addAiLog('AI co-pilot resting. Manual mode enabled.', 'warning');
          return ['AI subsystem suspended'];
        }
        case 'task': {
          if (!payload) {
            return ['ai task: please describe the mission'];
          }
          const task: AiTask = {
            id: uniqueId(),
            description: payload,
            status: aiActive ? 'running' : 'queued',
            createdAt: Date.now()
          };
          setAiTasks((prev) => [task, ...prev].slice(0, 12));
          addAiLog(`Task queued: ${payload}`, 'info');
          return [`Queued AI mission: ${payload}`];
        }
        case 'analyze': {
          const loadIndicator = systemStats.cpu > 72 ? 'High load' : systemStats.cpu > 55 ? 'Moderate load' : 'Stable';
          const repoHeadline = gitRepos
            .map((repo) => `${repo.name}:${repo.status}`)
            .join(' • ');
          addAiLog('AI diagnostic sweep completed.', 'info');
          return [
            `Telemetry: CPU ${systemStats.cpu.toFixed(1)}%, MEM ${systemStats.memory.toFixed(1)}% (${loadIndicator})`,
            `Repos: ${repoHeadline}`
          ];
        }
        case 'optimize': {
          setSystemStats((prev) => ({
            cpu: clamp(prev.cpu - 4, 5, 96),
            memory: clamp(prev.memory - 2, 12, 95),
            networkIn: prev.networkIn,
            networkOut: prev.networkOut + 1.2,
            temperature: clamp(prev.temperature - 1.5, 45, 84)
          }));
          addAiLog('Optimization pulse applied to telemetry.', 'success');
          return ['Optimization pulse sent to telemetry'];
        }
        default: {
          return ['Unknown AI directive. Try ai status|activate|deactivate|task|analyze|optimize'];
        }
      }
    },
    [aiTasks, aiActive, addAiLog, systemStats, gitRepos]
  );

  const handleCommand = useCallback(
    (input: string) => {
      const trimmed = input.trim();
      if (!trimmed) {
        return;
      }
      const session = terminalSessions['term-0'];
      if (!session) {
        return;
      }

      if (trimmed === 'clear') {
        setTerminalSessions((prev) => ({
          ...prev,
          'term-0': {
            ...session,
            history: []
          }
        }));
        return;
      }

      let result: CommandResult;
      if (trimmed.startsWith('ai ')) {
        const aiOutput = handleAiCommand(trimmed);
        result = {
          output: aiOutput,
          newPath: session.path,
          fileSystem
        };
      } else {
        result = runCommand(trimmed, session, fileSystem);
      }

      if (result.fileSystem !== fileSystem) {
        setFileSystem(result.fileSystem);
      }

      setTerminalSessions((prev) => ({
        ...prev,
        'term-0': {
          ...session,
          path: result.newPath,
          history: [...session.history, `${session.path}$ ${trimmed}`, ...result.output]
        }
      }));
    },
    [terminalSessions, fileSystem, handleAiCommand]
  );

  const handleTerminalSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      handleCommand(commandInput);
      setCommandInput('');
    },
    [commandInput, handleCommand]
  );

  const handleRunCode = useCallback(() => {
    const output = executeCode(codeInput, codeLanguage);
    setCodeOutput(output);
  }, [codeInput, codeLanguage]);

  const handleNavigate = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const url = browserUrl.trim() || 'about:blank';
      setBrowserHistory((prev) => [{ url, timestamp: Date.now() }, ...prev].slice(0, 8));
      addAiLog(`Browser ping: ${url}`, 'info');
    },
    [browserUrl, addAiLog]
  );

  return (
    <div className="echo-control-center">
      <div className="ecc-grid">
        <section className="ecc-panel ecc-panel--wide">
          <header>
            <span>Operational Snapshot</span>
            <span>{snapshot.averageActivity.toFixed(0)}% avg cadence</span>
          </header>
          <div className="ecc-snapshot">
            <div>
              <strong>{snapshot.total}</strong>
              <span>Active repos</span>
            </div>
            <div>
              <strong>{snapshot.modified}</strong>
              <span>Modified</span>
            </div>
            <div>
              <strong>{snapshot.staged}</strong>
              <span>Staged</span>
            </div>
            <div>
              <strong>{snapshot.behind}</strong>
              <span>Behind remote</span>
            </div>
          </div>
        </section>

        <section className="ecc-panel ecc-panel--wide">
          <header>
            <span>Repository Activity</span>
            <span>{new Date().toLocaleTimeString()}</span>
          </header>
          <div className="ecc-repo-grid">
            {gitRepos.map((repo) => {
              const style = statusStyles[repo.status];
              return (
                <article key={repo.name} className="ecc-repo-card">
                  <div className="ecc-repo-header">
                    <div>
                      <h3>{repo.name}</h3>
                      <p className="ecc-repo-branch">{repo.branch}</p>
                    </div>
                    <span
                      className="ecc-status"
                      style={{
                        backgroundColor: style.background,
                        borderColor: style.border,
                        color: style.color
                      }}
                    >
                      {repo.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="ecc-repo-meta">
                    {repo.commits} commits • {statusMessage(repo.status)}
                  </p>
                  <p className="ecc-repo-meta">Last commit {formatRelativeTime(repo.lastCommitTs)}</p>
                  <div className="ecc-progress">
                    <div className="ecc-progress__label">
                      <span>Activity</span>
                      <span>{Math.round(repo.activity * 100)}%</span>
                    </div>
                    <div className="ecc-progress__bar">
                      <div className="ecc-progress__bar-fill" style={{ width: `${repo.activity * 100}%` }} />
                    </div>
                  </div>
                  {repo.blockers > 0 ? (
                    <p className="ecc-repo-warning">{repo.blockers} blockers flagged</p>
                  ) : (
                    <p className="ecc-repo-success">No blockers detected</p>
                  )}
                </article>
              );
            })}
          </div>
        </section>

        <section className="ecc-panel">
          <header>
            <span>System Telemetry</span>
            <span>{systemStats.temperature.toFixed(1)}°C</span>
          </header>
          <div className="ecc-stats">
            <StatBar label="CPU" value={systemStats.cpu} />
            <StatBar label="Memory" value={systemStats.memory} />
            <StatBar label="Network In" value={systemStats.networkIn * 1.4} />
            <StatBar label="Network Out" value={systemStats.networkOut * 1.6} />
          </div>
          <p className="ecc-telemetry-note">
            Live telemetry is simulated for control center preview purposes.
          </p>
        </section>

        <section className="ecc-panel ecc-panel--wide ecc-panel--terminal">
          <header>
            <span>EchoOS Terminal</span>
            <span>{isBooted ? 'Ready' : `Booting (${bootStage}/${BOOT_SEQUENCE.length})`}</span>
          </header>
          <div ref={terminalRef} className="ecc-terminal">
            {terminalSessions['term-0']?.history.map((line, index) => (
              <div key={`term-line-${index}`}>{line}</div>
            ))}
          </div>
          <form className="ecc-terminal-input" onSubmit={handleTerminalSubmit}>
            <span>{terminalSessions['term-0']?.path}$</span>
            <input
              value={commandInput}
              onChange={(event) => setCommandInput(event.target.value)}
              placeholder="Type a command (try help)"
              spellCheck={false}
            />
            <button type="submit">Execute</button>
          </form>
        </section>

        <section className="ecc-panel ecc-panel--wide">
          <header>
            <span>Code Execution Sandbox</span>
            <span>{codeLanguage.toUpperCase()}</span>
          </header>
          <div className="ecc-code-runner">
            <textarea
              value={codeInput}
              onChange={(event) => setCodeInput(event.target.value)}
              spellCheck={false}
            />
            <div className="ecc-code-controls">
              <select value={codeLanguage} onChange={(event) => setCodeLanguage(event.target.value as 'javascript' | 'python')}>
                <option value="javascript">JavaScript</option>
                <option value="python">Python</option>
              </select>
              <button type="button" onClick={handleRunCode}>
                Run
              </button>
            </div>
            <pre className="ecc-code-output">{codeOutput || 'Output will appear here.'}</pre>
          </div>
        </section>

        <section className="ecc-panel">
          <header>
            <span>Browser Probe</span>
            <span>{browserHistory.length ? formatRelativeTime(browserHistory[0].timestamp) : 'Idle'}</span>
          </header>
          <form className="ecc-browser" onSubmit={handleNavigate}>
            <input value={browserUrl} onChange={(event) => setBrowserUrl(event.target.value)} placeholder="https://" />
            <button type="submit">Ping</button>
          </form>
          <ul className="ecc-browser-history">
            {browserHistory.length === 0 ? <li>No navigation recorded</li> : null}
            {browserHistory.map((entry, index) => (
              <li key={`${entry.url}-${index}`}>
                <span>{entry.url}</span>
                <time>{formatRelativeTime(entry.timestamp)}</time>
              </li>
            ))}
          </ul>
        </section>

        <section className="ecc-panel">
          <header>
            <span>AI Co-Pilot</span>
            <AiStatusPill active={aiActive} />
          </header>
          <div className="ecc-ai-controls">
            <button type="button" onClick={() => setAiActive((value) => !value)}>
              {aiActive ? 'Deactivate' : 'Activate'}
            </button>
            <span>{summarizeTasks(aiTasks)}</span>
          </div>
          <ul className="ecc-ai-log">
            {aiLog.length === 0 ? <li>No AI events yet</li> : null}
            {aiLog.slice(0, 6).map((entry, index) => (
              <li key={`${entry.timestamp}-${index}`} className={`ecc-ai-log__${entry.type}`}>
                <span>{entry.message}</span>
                <time>{entry.timestamp}</time>
              </li>
            ))}
          </ul>
          <ul className="ecc-ai-tasks">
            {aiTasks.slice(0, 5).map((task) => (
              <li key={task.id}>
                <span>{task.description}</span>
                <TaskPill status={task.status} />
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
};

export default EchoControlCenter;
