import Link from 'next/link';
import type { CodexItem } from '../lib/types';

interface Props {
  items: CodexItem[];
  generatedAt?: string;
}

function formatRelativeTime(iso?: string) {
  if (!iso) return 'unknown';
  try {
    const date = new Date(iso);
    return date.toLocaleString();
  } catch (error) {
    return iso;
  }
}

export default function CodexSummaryCard({ items, generatedAt }: Props) {
  const top = items.slice(0, 4);

  return (
    <article className="card flex flex-col justify-between overflow-hidden border border-slate-800/60 bg-slate-950/50">
      <div className="flex flex-col gap-4 p-5">
        <header className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Codex Pulse</h2>
            <p className="text-sm text-slate-400">Latest merged rituals from the Echo Codex registry.</p>
          </div>
          <span className="rounded-full border border-echo-ember/40 bg-echo-ember/10 px-3 py-1 text-xs uppercase tracking-wide text-echo-ember">
            Updated {formatRelativeTime(generatedAt)}
          </span>
        </header>
        <ul className="flex flex-col gap-3 text-sm">
          {top.map((item) => (
            <li key={item.id} className="rounded-lg border border-slate-800/60 bg-slate-900/40 p-3">
              <p className="font-medium text-white">{item.title}</p>
              <p className="text-xs text-slate-400">#{item.id} · {item.labels.join(', ') || 'untagged'}</p>
              <p className="mt-2 text-xs text-slate-300">{item.summary}</p>
            </li>
          ))}
          {!top.length && <li className="text-slate-500">No merged pull requests recorded yet.</li>}
        </ul>
      </div>
      <footer className="border-t border-slate-800/60 bg-slate-900/60 p-4 text-right">
        <Link
          href="/codex"
          className="inline-flex items-center justify-center rounded-md border border-echo-ember/70 bg-echo-ember/10 px-4 py-2 text-sm font-medium text-echo-ember transition hover:bg-echo-ember/20"
        >
          View Codex Timeline
        </Link>
      </footer>
    </article>
  );
}
