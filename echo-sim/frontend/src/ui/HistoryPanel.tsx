import type { HistoryItem } from '../state';

const iconByKind: Record<HistoryItem['kind'], string> = {
  chat: '💬',
  code: '💻',
  event: '🌠',
};

type Props = {
  history: HistoryItem[];
};

export function HistoryPanel({ history }: Props) {
  return (
    <section className="panel" aria-label="Echo timeline">
      <div className="gradient-sheen" aria-hidden />
      <h2>Activity Timeline</h2>
      <div className="history-list">
        {history
          .slice()
          .sort((a, b) => b.ts - a.ts)
          .slice(0, 12)
          .map((entry) => (
            <article key={`${entry.kind}-${entry.ts}`} className="history-item">
              <span aria-hidden>{iconByKind[entry.kind]}</span>
              <div>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#e2e8f0' }}>{entry.text}</p>
                <time style={{ fontSize: '0.7rem', color: '#64748b' }}>{new Date(entry.ts).toLocaleTimeString()}</time>
              </div>
            </article>
          ))}
      </div>
    </section>
  );
}
