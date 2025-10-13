import type { MemoryItem } from '../state';

type Props = {
  memories: MemoryItem[];
};

export function MemoryPanel({ memories }: Props) {
  return (
    <section className="panel" aria-label="Echo memory archive">
      <div className="gradient-sheen" aria-hidden />
      <h2>Echo’s Memory</h2>
      <div className="memory-list">
        {memories
          .slice()
          .sort((a, b) => b.ts - a.ts)
          .map((memory) => (
            <article key={memory.key} className="memory-item">
              <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ color: '#22d3ee', fontSize: '0.75rem', letterSpacing: '0.08em' }}>{memory.key}</span>
                <time style={{ color: '#38bdf8', fontSize: '0.7rem' }}>{new Date(memory.ts).toLocaleTimeString()}</time>
              </header>
              <p style={{ margin: '0.35rem 0 0', fontSize: '0.85rem', color: '#e2e8f0' }}>{memory.value}</p>
            </article>
          ))}
      </div>
    </section>
  );
}
