import { useEffect, useMemo, useState } from 'react';
import mermaid from 'mermaid';
import { useDashboard } from './store';

const METRICS_WS = 'ws://localhost:9101';
const API_BASE = 'http://localhost:8000/api';

function useMermaid(diagram: string) {
  const [svg, setSvg] = useState('');

  useEffect(() => {
    let cancelled = false;
    mermaid.render('atlas-graph', diagram).then(({ svg }) => {
      if (!cancelled) {
        setSvg(svg);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [diagram]);

  return svg;
}

export default function App() {
  const { metrics, nodes, queue, setMetrics, setNodes, setQueue } = useDashboard();

  useEffect(() => {
    const ws = new WebSocket(METRICS_WS);
    ws.onmessage = (event) => {
      const snapshot = JSON.parse(event.data);
      setMetrics(snapshot);
    };
    ws.onerror = () => {
      ws.close();
    };
    return () => ws.close();
  }, [setMetrics]);

  useEffect(() => {
    const load = async () => {
      try {
        const [nodeRes, queueRes] = await Promise.all([
          fetch(`${API_BASE}/nodes`).then((res) => res.json()),
          fetch(`${API_BASE}/scheduler/due`).then((res) => res.json()),
        ]);
        setNodes(nodeRes);
        setQueue(queueRes);
      } catch (err) {
        console.warn('Failed to load API data', err);
      }
    };
    load();
  }, [setNodes, setQueue]);

  const graph = useMemo(() => {
    if (!nodes.length) {
      return 'graph TD; A[No Nodes]';
    }
    const edges = nodes
      .map((node) => `Atlas-->${node.id}`)
      .join('\n  ');
    return `graph TD\n  ${edges}`;
  }, [nodes]);

  const svg = useMermaid(graph);

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', padding: '1rem', display: 'grid', gap: '1rem' }}>
      <header>
        <h1>Atlas Control Plane</h1>
        <p>Live metrics, topology, and queue status.</p>
      </header>
      <section>
        <h2>Metrics</h2>
        {metrics ? (
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
        ) : (
          <p>No metrics yet. Ensure the metrics service is running.</p>
        )}
      </section>
      <section>
        <h2>Node Graph</h2>
        <div dangerouslySetInnerHTML={{ __html: svg }} />
      </section>
      <section>
        <h2>Job Queue</h2>
        {queue.length ? (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Tenant</th>
                <th>Status</th>
                <th>Schedule</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((job) => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td>{job.tenant}</td>
                  <td>{job.status}</td>
                  <td>{new Date(job.schedule_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No jobs currently due.</p>
        )}
      </section>
      <section>
        <h2>Storage Stats</h2>
        <p>Use the CLI to store objects and view receipts. Dashboard integration polls `atlas storage` receipts.</p>
      </section>
    </div>
  );
}
