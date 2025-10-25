import { useCallback, useMemo, useState } from 'react';
import Constellation, {
  GraphEdge,
  GraphMeta,
  GraphNode,
  Selection,
} from './components/Constellation';

import './app.css';
import PulseForge from './components/PulseForge';

const typeLabels: Record<string, string> = {
  repo: 'Repository',
  commit: 'Commit',
  pr: 'Pull Request',
  module: 'Module',
  symbol: 'Symbol',
  artifact: 'Artifact',
};

function formatTimestamp(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function dedupe<T>(items: T[]): T[] {
  return Array.from(new Set(items));
}

function renderDetails(node: GraphNode | null, edges: GraphEdge[]): JSX.Element | null {
  if (!node) {
    return null;
  }

  const heading = typeLabels[node.type] ?? node.type;
  const data = node.data ?? {};

  if (node.type === 'commit') {
    const files = Array.isArray(data.files) ? (data.files as unknown as string[]) : [];
    return (
      <div>
        <h2>{heading}</h2>
        <p className="muted">{node.id.replace('commit:', '')}</p>
        <p>{data.message as string}</p>
        <dl>
          <dt>Author</dt>
          <dd>{(data.author as string) ?? 'unknown'}</dd>
          <dt>Timestamp</dt>
          <dd>{formatTimestamp(data.timestamp)}</dd>
        </dl>
        <h3>Files</h3>
        <ul>
          {files.map((file) => (
            <li key={file}>{file}</li>
          ))}
        </ul>
      </div>
    );
  }

  if (node.type === 'pr') {
    const url = typeof data.url === 'string' ? data.url : null;
    return (
      <div>
        <h2>{heading}</h2>
        <p className="muted">{data.label as string}</p>
        <p>Status: {(data.status as string) ?? 'unknown'}</p>
        {url ? (
          <p>
            <a href={url} target="_blank" rel="noreferrer">
              View on GitHub
            </a>
          </p>
        ) : null}
      </div>
    );
  }

  if (node.type === 'repo') {
    const remote = typeof data.remote === 'string' ? data.remote : null;
    return (
      <div>
        <h2>{heading}</h2>
        <p className="muted">{data.path as string}</p>
        {remote ? (
          <p>
            <a href={remote} target="_blank" rel="noreferrer">
              Remote Repository
            </a>
          </p>
        ) : null}
      </div>
    );
  }

  if (node.type === 'artifact') {
    const headingLabel = typeof data.heading === 'string' ? data.heading : null;
    const path = typeof data.path === 'string' ? data.path : null;
    return (
      <div>
        <h2>{heading}</h2>
        {headingLabel ? <p className="muted">{headingLabel}</p> : null}
        {path ? <p>{path}</p> : null}
      </div>
    );
  }

  if (node.type === 'module') {
    return (
      <div>
        <h2>{heading}</h2>
        <p>{data.module as string}</p>
      </div>
    );
  }

  if (node.type === 'symbol') {
    return (
      <div>
        <h2>{heading}</h2>
        <p>
          {(data.module as string) ?? 'module'}.<strong>{data.name as string}</strong>
        </p>
      </div>
    );
  }

  const relatedIds = dedupe(
    edges.flatMap((edge) => [edge.source, edge.target]).filter((id) => id !== node.id),
  );

  return (
    <div>
      <h2>{heading}</h2>
      <p>{node.id}</p>
      {relatedIds.length ? (
        <>
          <h3>Connected</h3>
          <ul>
            {relatedIds.map((id) => (
              <li key={id}>{id}</li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}

export default function App(): JSX.Element {
  const [selection, setSelection] = useState<Selection | null>(null);
  const [meta, setMeta] = useState<GraphMeta | null>(null);

  const handleSelect = useCallback((payload: Selection | null) => {
    setSelection(payload);
  }, []);

  const rightPanel = useMemo(() => {
    if (!selection) {
      return (
        <div className="placeholder">
          <h2>Explore the Echo Constellation</h2>
          <p>Select a node to view its details.</p>
        </div>
      );
    }

    return <div>{renderDetails(selection.node, selection.edges)}</div>;
  }, [selection]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Echo Constellation</h1>
          <p className="subtitle">Interactive map of Echo commits, artifacts, and modules.</p>
        </div>
        {meta?.next_step ? <div className="badge">{meta.next_step}</div> : null}
      </header>
      <main className="app-main">
        <div className="graph-pane">
          <Constellation onSelect={handleSelect} onMeta={setMeta} />
        </div>
        <aside className="details-pane">{rightPanel}</aside>
      </main>
      <section className="pulseforge-section">
        <h2>🌌 Echo Codex PulseForge</h2>
        <p className="muted">
          Every merged pull request becomes a living glyph. Watch contract classes pulse as Echo evolves.
        </p>
        <PulseForge />
      </section>
    </div>
  );
}
