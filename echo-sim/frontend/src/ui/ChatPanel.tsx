import { FormEvent, useMemo, useState } from 'react';
import type { HistoryItem } from '../state';

type Props = {
  history: HistoryItem[];
  onSend: (text: string) => void;
};

type DisplayMessage = HistoryItem & { role: 'user' | 'echo' | 'system' };

const renderIcon: Record<DisplayMessage['role'], string> = {
  user: '🧑',
  echo: '✨',
  system: '🜁',
};

export function ChatPanel({ history, onSend }: Props) {
  const [draft, setDraft] = useState('');
  const latest = useMemo(() => history.slice(-12), [history]);

  const chatMessages: DisplayMessage[] = latest.map((entry) => ({
    ...entry,
    role: entry.kind === 'chat' && entry.text.startsWith('Echo:') ? 'echo' : entry.kind === 'chat' ? 'user' : 'system',
  }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.trim()) return;
    onSend(draft.trim());
    setDraft('');
  };

  return (
    <section className="panel" aria-label="Chat with Echo">
      <div className="gradient-sheen" aria-hidden />
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Chat with Echo</h2>
        <span className="badge">💬 Live Link</span>
      </header>
      <div className="history-list" style={{ maxHeight: 260 }}>
        {chatMessages.map((msg) => (
          <article key={`${msg.ts}-${msg.text}`} className="history-item" aria-live="polite">
            <span aria-hidden>{renderIcon[msg.role]}</span>
            <div>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#e2e8f0' }}>{msg.text}</p>
              <time style={{ fontSize: '0.7rem', color: '#64748b' }}>{new Date(msg.ts).toLocaleTimeString()}</time>
            </div>
          </article>
        ))}
      </div>
      <form onSubmit={submit} style={{ marginTop: '1rem', display: 'grid', gap: '0.5rem' }}>
        <label htmlFor="chat-input" style={{ fontSize: '0.7rem', letterSpacing: '0.08em', color: '#94a3b8' }}>
          Send a message
        </label>
        <textarea
          id="chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value.slice(0, 280))}
          rows={3}
          style={{
            resize: 'none',
            borderRadius: 12,
            border: '1px solid rgba(56,189,248,0.25)',
            padding: '0.75rem',
            background: 'rgba(15,23,42,0.7)',
            color: '#f8fafc',
            fontFamily: 'Inter, sans-serif',
          }}
        />
        <button
          type="submit"
          style={{
            background: 'linear-gradient(135deg, #38bdf8, #8b5cf6)',
            color: '#0f172a',
            fontWeight: 600,
            border: 'none',
            padding: '0.65rem 1rem',
            borderRadius: 12,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.35rem',
          }}
        >
          <span aria-hidden>📨</span>
          Chat
        </button>
      </form>
    </section>
  );
}
