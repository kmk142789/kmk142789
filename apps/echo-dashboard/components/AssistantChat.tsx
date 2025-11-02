'use client';

import { useState } from 'react';
import { apiPost } from '../lib/api';
import type { AssistantResponse } from '../lib/types';

interface ConversationEntry {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: AssistantResponse;
}

function formatArgs(args: Record<string, unknown> = {}) {
  return Object.entries(args)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(', ');
}

function generateId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

export default function AssistantChat() {
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!message.trim()) return;
    const userEntry: ConversationEntry = {
      id: generateId(),
      role: 'user',
      content: message.trim(),
    };
    setConversation((prev) => [...prev, userEntry]);
    setMessage('');
    setLoading(true);
    setError(null);

    try {
      const response = await apiPost<AssistantResponse>('/assistant/chat', { message: userEntry.content });
      const assistantEntry: ConversationEntry = {
        id: generateId(),
        role: 'assistant',
        content: response.message,
        response,
      };
      setConversation((prev) => [...prev, assistantEntry]);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unexpected error calling assistant.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <header>
        <p className="badge text-echo-ember">EchoComputerAssistant</p>
        <h1 className="text-3xl font-semibold text-white">Tool-Enabled Chat</h1>
        <p className="text-slate-300">Ask questions about puzzles, Echo Bank rituals, or Codex activity. Tool calls and sandbox logs are streamed below.</p>
      </header>

      <section className="flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-950/70 p-6">
        <div className="flex flex-col gap-4">
          {conversation.map((entry) => (
            <article
              key={entry.id}
              className={`rounded-lg border px-4 py-3 text-sm ${
                entry.role === 'user'
                  ? 'border-echo-ember/40 bg-echo-ember/10 text-echo-ember'
                  : 'border-slate-800 bg-slate-900/70 text-slate-200'
              }`}
            >
              <header className="mb-2 flex items-center justify-between text-xs uppercase tracking-wide">
                <span>{entry.role === 'user' ? 'User' : 'Assistant'}</span>
                {entry.response && <span className="text-slate-400">Function: {entry.response.function}</span>}
              </header>
              <p className="whitespace-pre-wrap text-sm">{entry.content}</p>
              {entry.response && (
                <div className="mt-3 flex flex-col gap-3 text-xs text-slate-300">
                  <div>
                    <p className="font-semibold text-slate-200">Tool arguments</p>
                    <p>{formatArgs(entry.response.arguments)}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-200">Logs</p>
                    <ul className="list-disc pl-4">
                      {entry.response.logs.map((log, index) => (
                        <li key={index}>{log}</li>
                      ))}
                      {!entry.response.logs.length && <li>No logs recorded.</li>}
                    </ul>
                  </div>
                  {entry.response.data && (
                    <div>
                      <p className="font-semibold text-slate-200">Result</p>
                      <pre className="overflow-auto rounded-md bg-slate-950/80 p-3 text-[11px] leading-relaxed text-slate-100">
                        {JSON.stringify(entry.response.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </article>
          ))}
          {!conversation.length && (
            <p className="text-sm text-slate-400">No conversations yet. Ask the assistant about a puzzle or request Codex entries.</p>
          )}
        </div>
        {error && <p className="text-xs text-rose-400">{error}</p>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 md:flex-row md:items-center">
          <input
            type="text"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="e.g. solve puzzle #96"
            className="flex-1 rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-white focus:border-echo-ember focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center rounded-md border border-echo-ember/60 bg-echo-ember/20 px-4 py-2 text-sm font-semibold text-echo-ember transition hover:bg-echo-ember/30 disabled:opacity-60"
          >
            {loading ? 'Calling tools…' : 'Send'}
          </button>
        </form>
      </section>
    </div>
  );
}
