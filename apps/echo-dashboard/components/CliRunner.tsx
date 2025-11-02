'use client';

import { FormEvent, useEffect, useState } from 'react';
import type { CliCommand, CliResult } from '../lib/types';

interface Props {
  commands: CliCommand[];
  onRun: (command: string, args: string[]) => Promise<void> | void;
  loading: boolean;
  result: CliResult | null;
}

const DEFAULT_ARGS: Record<string, string> = {
  refresh: '--json',
  verify: '--json',
  stats: '--json',
  export: '--json',
  'enrich-ud': '--json',
  transcend: '--json',
};

export default function CliRunner({ commands, onRun, loading, result }: Props) {
  const [command, setCommand] = useState(commands[0]?.value ?? 'refresh');
  const [args, setArgs] = useState(DEFAULT_ARGS[command] ?? '');

  useEffect(() => {
    if (!commands.length) return;
    setCommand((current) => {
      if (commands.some((item) => item.value === current)) {
        return current;
      }
      const next = commands[0].value;
      setArgs(DEFAULT_ARGS[next] ?? '');
      return next;
    });
  }, [commands]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!command) return;
    const parsedArgs = args
      .split(/\s+/)
      .map((value) => value.trim())
      .filter(Boolean);
    await onRun(command, parsedArgs);
  };

  return (
    <article className="card flex flex-col overflow-hidden">
      <header className="border-b border-slate-800 px-5 py-4">
        <h2 className="text-lg font-semibold text-white">Echo CLI Bridge</h2>
        <p className="text-sm text-slate-400">Launch curated `echo_cli` rituals straight from the dashboard.</p>
      </header>
      <div className="flex flex-1 flex-col gap-4 p-5">
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-slate-300">Command</span>
            <select
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-pulse focus:outline-none"
              value={command}
              onChange={(event) => {
                const value = event.target.value;
                setCommand(value);
                setArgs(DEFAULT_ARGS[value] ?? '');
              }}
            >
              {commands.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-slate-300">Arguments</span>
            <input
              type="text"
              value={args}
              onChange={(event) => setArgs(event.target.value)}
              placeholder="--json"
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-pulse focus:outline-none"
            />
          </label>
          <button
            type="submit"
            disabled={loading || !commands.length}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-echo-pulse px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Running…' : 'Run command'}
          </button>
        </form>
        <section className="flex flex-1 flex-col gap-3">
          <header className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Output</h3>
            {result && (
              <span className="badge border border-slate-700 text-slate-300">Exit {result.code ?? '—'}</span>
            )}
          </header>
          <pre className="min-h-[10rem] flex-1 overflow-y-auto rounded-lg bg-slate-950/80 p-4 text-xs leading-relaxed text-slate-200">
            {result ? `${result.stdout}${result.stderr ? `\n--- stderr ---\n${result.stderr}` : ''}` : 'Awaiting ritual.'}
          </pre>
        </section>
      </div>
    </article>
  );
}
