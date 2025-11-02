'use client';

import { FormEvent, useMemo, useState } from 'react';
import type { NeonKeyRecord } from '../lib/types';

interface Props {
  records: NeonKeyRecord[];
  error: string | null;
  onCreate: (label: string, value: string) => Promise<void> | void;
  onDelete: (id: string) => Promise<void> | void;
}

export default function NeonKeyManager({ records, error, onCreate, onDelete }: Props) {
  const [label, setLabel] = useState('');
  const [value, setValue] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const sortedRecords = useMemo(
    () => [...records].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [records]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback(null);
    try {
      await onCreate(label, value);
      setLabel('');
      setValue('');
      setFeedback('Neon key secured.');
    } catch (err) {
      if (err instanceof Error) {
        setFeedback(
          err.message === 'invalid_encryption_key'
            ? 'Set NEON_KEY_ENCRYPTION_KEY to at least 16 characters before storing keys.'
            : err.message
        );
      } else {
        setFeedback('Failed to store Neon key.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <article className="card flex flex-col overflow-hidden">
      <header className="border-b border-slate-800 px-5 py-4">
        <h2 className="text-lg font-semibold text-white">Neon Vault</h2>
        <p className="text-sm text-slate-400">
          Encrypt Neon API keys using AES-256-GCM before persisting to your Postgres orbit.
        </p>
      </header>
      <div className="flex flex-1 flex-col gap-4 p-5">
        {error ? (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-200">
            {error}
          </div>
        ) : (
          <>
            <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
              <label className="flex flex-col gap-2 text-sm">
                <span className="text-slate-300">Label</span>
                <input
                  type="text"
                  value={label}
                  onChange={(event) => setLabel(event.target.value)}
                  placeholder="Production orchestrator"
                  className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-ember focus:outline-none"
                />
              </label>
              <label className="flex flex-col gap-2 text-sm">
                <span className="text-slate-300">API Key</span>
                <input
                  type="password"
                  value={value}
                  onChange={(event) => setValue(event.target.value)}
                  placeholder="neon_secret_..."
                  className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-ember focus:outline-none"
                />
              </label>
              <button
                type="submit"
                disabled={submitting || !label || !value}
                className="inline-flex items-center justify-center gap-2 rounded-md bg-echo-ember px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-pink-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? 'Encrypting…' : 'Store key securely'}
              </button>
              {feedback && <p className="text-xs text-slate-400">{feedback}</p>}
            </form>
            <section className="flex flex-1 flex-col gap-3">
              <header className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Stored keys</h3>
                <span className="badge text-slate-300">{sortedRecords.length} active</span>
              </header>
              <ul className="flex flex-col gap-3 text-sm">
                {sortedRecords.map((record) => (
                  <li key={record.id} className="flex flex-col gap-2 rounded-lg border border-slate-800 bg-slate-900/70 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-white">{record.label}</p>
                        <p className="text-xs text-slate-400">
                          Created {new Date(record.created_at).toLocaleString()} · ending {record.last_four}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => onDelete(record.id)}
                        className="rounded-md border border-rose-500/40 px-3 py-1 text-xs font-medium text-rose-200 hover:bg-rose-500/20"
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
                {!sortedRecords.length && (
                  <li className="rounded-lg border border-dashed border-slate-700 bg-slate-900/60 p-6 text-center text-xs text-slate-400">
                    No Neon keys stored yet.
                  </li>
                )}
              </ul>
            </section>
          </>
        )}
      </div>
    </article>
  );
}
