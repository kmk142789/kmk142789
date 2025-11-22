import { useEffect, useMemo, useState } from 'react';
import mermaid from 'mermaid';
import { useDashboard } from './store';
import type {
  AmendmentRecord,
  BridgeLog,
  CredentialEvent,
  LedgerAction,
  PlanRecord,
  ProofRecord,
} from './store';

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
  const {
    metrics,
    nodes,
    queue,
    credentials,
    ledgerActions,
    proofs,
    amendments,
    plans,
    bridgeLogs,
    setMetrics,
    setNodes,
    setQueue,
    setCredentials,
    setLedgerActions,
    setProofs,
    setAmendments,
    setPlans,
    setBridgeLogs,
  } = useDashboard();

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

  useEffect(() => {
    const rollupFallbacks = {
      credentials: [
        { id: 'vc-901', subject: 'did:example:issuer', status: 'issued', issued_at: new Date().toISOString() },
        { id: 'vc-902', subject: 'did:example:holder', status: 'verified', issued_at: new Date(Date.now() - 3600 * 1000).toISOString() },
      ] satisfies CredentialEvent[],
      ledgerActions: [
        { id: 'tx-711', action: 'Mint', network: 'L1-Atlas', status: 'finalized', timestamp: new Date().toISOString() },
        { id: 'tx-712', action: 'Bridge', network: 'L2-Orbital', status: 'pending', timestamp: new Date(Date.now() - 7200 * 1000).toISOString() },
      ] satisfies LedgerAction[],
      proofs: [
        { id: 'proof-44', type: 'ZK-Receipt', anchor: 'Keccak', status: 'valid', timestamp: new Date().toISOString() },
        { id: 'proof-45', type: 'SNARK', anchor: 'Poseidon', status: 'pending', timestamp: new Date(Date.now() - 1800 * 1000).toISOString() },
      ] satisfies ProofRecord[],
      amendments: [
        { id: 'amd-21', title: 'Sovereign Charter IV', status: 'adopted', updated_at: new Date().toISOString() },
        { id: 'amd-22', title: 'Validator Rotation', status: 'in review', updated_at: new Date(Date.now() - 5400 * 1000).toISOString() },
      ] satisfies AmendmentRecord[],
      plans: [
        { id: 'plan-08', name: 'Autonomous Treasury', stage: 'orchestration', next_step: 'Activate streaming safeguards' },
        { id: 'plan-09', name: 'Bridge Sentinel', stage: 'analysis', next_step: 'Replay cross-ledger logs' },
      ] satisfies PlanRecord[],
      bridgeLogs: [
        { id: 'bridge-301', source: 'L2-Orbital', destination: 'L1-Atlas', status: 'settled', height: 190212 },
        { id: 'bridge-302', source: 'L1-Atlas', destination: 'zkSync', status: 'queued', height: 190214 },
      ] satisfies BridgeLog[],
    };

    const fetchJson = async <T,>(url: string, fallback: T): Promise<T> => {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return (await response.json()) as T;
      } catch (err) {
        console.warn(`Falling back for ${url}`, err);
        return fallback;
      }
    };

    const loadRollup = async () => {
      const [vcData, ledgerData, proofData, amendmentData, planData, bridgeData] = await Promise.all([
        fetchJson(`${API_BASE}/credentials`, rollupFallbacks.credentials),
        fetchJson(`${API_BASE}/ledger/actions`, rollupFallbacks.ledgerActions),
        fetchJson(`${API_BASE}/proofs`, rollupFallbacks.proofs),
        fetchJson(`${API_BASE}/amendments`, rollupFallbacks.amendments),
        fetchJson(`${API_BASE}/plans`, rollupFallbacks.plans),
        fetchJson(`${API_BASE}/bridges/logs`, rollupFallbacks.bridgeLogs),
      ]);

      setCredentials(vcData);
      setLedgerActions(ledgerData);
      setProofs(proofData);
      setAmendments(amendmentData);
      setPlans(planData);
      setBridgeLogs(bridgeData);
    };

    loadRollup();
  }, [setCredentials, setLedgerActions, setProofs, setAmendments, setPlans, setBridgeLogs]);

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

  const formatTime = (value: string | number) => new Date(value).toLocaleString();

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', padding: '1rem', display: 'grid', gap: '1rem' }}>
      <header>
        <p style={{ textTransform: 'uppercase', letterSpacing: '0.08em', color: '#4f46e5', margin: 0 }}>
          Cross-Ledger Rollup
        </p>
        <h1 style={{ margin: '0.25rem 0' }}>Unified Atlas Operations Dashboard</h1>
        <p style={{ margin: 0, color: '#475569' }}>
          VC issuing, ledger actions, proofs, amendments, autonomous plans, and bridge logs in one pane of glass.
        </p>
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
      <section style={{ display: 'grid', gap: '1rem' }}>
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <article style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>VC Issuing</h3>
            <p style={{ margin: '0 0 0.5rem', color: '#475569' }}>Recent credential issuance and verification outcomes.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' }}>
              {credentials.map((vc) => (
                <li key={vc.id} style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{vc.id}</div>
                  <div style={{ color: '#475569' }}>{vc.subject}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#0f172a' }}>
                    <span>Status: {vc.status}</span>
                    <span>{formatTime(vc.issued_at)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
          <article style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>Ledger Actions</h3>
            <p style={{ margin: '0 0 0.5rem', color: '#475569' }}>Cross-ledger transactions and their current settlement state.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' }}>
              {ledgerActions.map((tx) => (
                <li key={tx.id} style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{tx.action}</div>
                  <div style={{ color: '#475569' }}>{tx.network}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#0f172a' }}>
                    <span>{tx.status}</span>
                    <span>{formatTime(tx.timestamp)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
          <article style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>Proofs</h3>
            <p style={{ margin: '0 0 0.5rem', color: '#475569' }}>Validity proofs anchored to cross-ledger receipts.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' }}>
              {proofs.map((proof) => (
                <li key={proof.id} style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{proof.type}</div>
                  <div style={{ color: '#475569' }}>Anchor: {proof.anchor}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#0f172a' }}>
                    <span>{proof.status}</span>
                    <span>{formatTime(proof.timestamp)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
          <article style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>Amendments</h3>
            <p style={{ margin: '0 0 0.5rem', color: '#475569' }}>Latest governance amendments rolled across ledgers.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' }}>
              {amendments.map((amd) => (
                <li key={amd.id} style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{amd.title}</div>
                  <div style={{ color: '#475569' }}>Status: {amd.status}</div>
                  <div style={{ color: '#0f172a' }}>{formatTime(amd.updated_at)}</div>
                </li>
              ))}
            </ul>
          </article>
          <article style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>Autonomous Plans</h3>
            <p style={{ margin: '0 0 0.5rem', color: '#475569' }}>Planner tracks for self-governing automation and next steps.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' }}>
              {plans.map((plan) => (
                <li key={plan.id} style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{plan.name}</div>
                  <div style={{ color: '#475569' }}>Stage: {plan.stage}</div>
                  <div style={{ color: '#0f172a' }}>Next: {plan.next_step}</div>
                </li>
              ))}
            </ul>
          </article>
          <article style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>Bridge Logs</h3>
            <p style={{ margin: '0 0 0.5rem', color: '#475569' }}>Rollup of bridge transfers and observed block heights.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.5rem' }}>
              {bridgeLogs.map((log) => (
                <li key={log.id} style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{log.source} → {log.destination}</div>
                  <div style={{ color: '#475569' }}>Height: {log.height}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#0f172a' }}>
                    <span>{log.status}</span>
                    <span>{typeof log.height === 'number' ? `#${log.height}` : ''}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>
    </div>
  );
}
