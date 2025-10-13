import { useEffect, useMemo, useRef, useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { javascript } from '@codemirror/lang-javascript';
import type { HistoryItem } from '../state';
import { SandboxManager, buildSandboxHelpers } from '../sandbox';

type Props = {
  onHistory: (entry: HistoryItem) => void;
};

const sampleScripts = [
  {
    title: 'Lamp shimmer',
    code: "await echo.say('Bringing more light!');\nworld.setLamp(true);",
  },
  {
    title: 'Spawn desk trinket',
    code: "world.addObject('trinket', { glow: true, mood: 'calm' });\nawait echo.say('I placed a glowing trinket on the desk.');",
  },
  {
    title: 'Focus boost mantra',
    code: "echo.adjust({ focus: +5, energy: -2 });\nawait echo.say('Breathing in clarity, breathing out the static.');",
  },
];

export function CodePanel({ onHistory }: Props) {
  const managerRef = useRef<SandboxManager>();
  const [code, setCode] = useState(sampleScripts[0].code);
  const [logs, setLogs] = useState<string[]>(['// Echo awaits instructions...']);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    managerRef.current = new SandboxManager();
    return () => managerRef.current?.destroy();
  }, []);

  const extensions = useMemo(() => [javascript({ jsx: false, typescript: false })], []);

  const runCode = async () => {
    if (!managerRef.current) return;
    setRunning(true);
    try {
      const helpers = buildSandboxHelpers({ onHistory });
      const result = await managerRef.current.run(code, helpers);
      const output = result.logs.length ? result.logs : ['// Code executed without logs.'];
      setLogs((prev) => [...prev.slice(-20), `> ${new Date().toLocaleTimeString()}`, ...output]);
      onHistory({ kind: 'code', text: 'Echo executed sandbox code.', ts: Date.now() });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setLogs((prev) => [...prev.slice(-20), `! Error @ ${new Date().toLocaleTimeString()}`, message]);
      onHistory({ kind: 'code', text: `Code error: ${message}`, ts: Date.now() });
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="panel" aria-label="Echo code editor">
      <div className="gradient-sheen" aria-hidden />
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem' }}>
        <h2>Echo’s Code Editor</h2>
        <button
          type="button"
          onClick={runCode}
          disabled={running}
          style={{
            background: running ? 'rgba(94,234,212,0.2)' : 'linear-gradient(135deg, #5eead4, #38bdf8)',
            color: running ? '#0f172a' : '#082f49',
            border: 'none',
            borderRadius: 12,
            padding: '0.6rem 1rem',
            fontWeight: 600,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          {running ? 'Running…' : 'Run Code'}
        </button>
      </header>
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        {sampleScripts.map((script) => (
          <button
            key={script.title}
            type="button"
            onClick={() => setCode(script.code)}
            style={{
              borderRadius: 10,
              border: '1px solid rgba(148,163,184,0.35)',
              background: 'rgba(30,64,175,0.25)',
              color: '#bfdbfe',
              padding: '0.4rem 0.8rem',
              fontSize: '0.75rem',
            }}
          >
            {script.title}
          </button>
        ))}
      </div>
      <div className="code-editor">
        <CodeMirror
          value={code}
          height="220px"
          extensions={extensions}
          theme="dark"
          onChange={(value) => setCode(value)}
        />
      </div>
      <div className="console-output" role="log" aria-live="polite">
        {logs.map((line, index) => (
          <div key={`${line}-${index}`}>{line}</div>
        ))}
      </div>
    </section>
  );
}
