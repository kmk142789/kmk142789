import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { GetServerSideProps, InferGetServerSidePropsType } from 'next';

type Direction = 'INFLOW' | 'OUTFLOW';

interface LedgerEvent {
  id: string;
  direction: Direction;
  amount_cents: number;
  currency: string;
  purpose?: string | null;
  source?: string | null;
  occurred_at: string;
  vc_id?: string | null;
  tags?: string[] | null;
  beneficiary?: string | null;
  narrative?: string | null;
  digest?: string | null;
  proof_path?: string | null;
  ots_receipt?: string | null;
}

interface DashboardProps {
  totals: {
    inflows: number;
    outflows: number;
    net: number;
  };
  events: LedgerEvent[];
  apiBaseUrl: string;
  generatedAt: string;
  governance: GovernanceAmendment[];
  audit: AuditTrail;
}

interface GovernanceAmendment {
  id: string;
  title: string;
  adopted_at: string;
  summary: string;
  proof_uri?: string;
  ratified_by?: string[];
  status?: string;
}

interface AuditTrailEntry {
  seq: number | null;
  digest?: string | null;
  direction?: string | null;
  amount?: string | null;
  asset?: string | null;
  timestamp?: string | null;
  proof_path?: string | null;
  ots_receipt?: string | null;
}

interface ContinuityCheckpoint {
  seq?: number | null;
  digest?: string | null;
  timestamp: string;
  threshold: number;
  trustees: string[];
}

interface AuditTrail {
  ledger: AuditTrailEntry[];
  continuity: ContinuityCheckpoint[];
}

interface LedgerStreamPayload {
  entry: LedgerEvent;
  totals: { inflows: number; outflows: number; net: number };
}

export const getServerSideProps: GetServerSideProps<DashboardProps> = async () => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:4000';
  const totalsUrl = `${baseUrl}/metrics/totals`;
  const eventsUrl = `${baseUrl}/ledger/events?limit=50`;
  const governanceUrl = `${baseUrl}/governance/amendments`;
  const auditUrl = `${baseUrl}/audit/trails?limit=20`;

  let totals = { inflows: 0, outflows: 0, net: 0 };
  let events: LedgerEvent[] = [];
  let governance: GovernanceAmendment[] = [];
  let audit: AuditTrail = { ledger: [], continuity: [] };

  try {
    const [totalsRes, eventsRes, governanceRes, auditRes] = await Promise.all([
      fetch(totalsUrl),
      fetch(eventsUrl),
      fetch(governanceUrl),
      fetch(auditUrl),
    ]);

    if (totalsRes.ok) {
      totals = await totalsRes.json();
    }

    if (eventsRes.ok) {
      events = await eventsRes.json();
    }

    if (governanceRes.ok) {
      const payload = await governanceRes.json();
      governance = payload.amendments ?? [];
    }

    if (auditRes.ok) {
      audit = await auditRes.json();
    }
  } catch (error) {
    console.error('Failed to reach issuer API', error);
  }

  return {
    props: {
      totals,
      events,
      apiBaseUrl: baseUrl,
      generatedAt: new Date().toISOString(),
      governance,
      audit,
    },
  };
};

function formatCurrency(cents: number, currency: string) {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format((cents ?? 0) / 100);
  } catch (error) {
    console.warn('Unable to format currency', error);
    return `${currency} ${(cents ?? 0) / 100}`;
  }
}

export default function DashboardPage({ totals, events, apiBaseUrl, generatedAt, governance, audit }: InferGetServerSidePropsType<typeof getServerSideProps>) {
  const trustRegistryUrl = process.env.NEXT_PUBLIC_TRUST_REGISTRY_URL ?? 'https://kmk142789.github.io/little-footsteps-bank/trust-registry.json';
  const [liveTotals, setLiveTotals] = useState(totals);
  const [liveEvents, setLiveEvents] = useState(events);

  useEffect(() => {
    setLiveTotals(totals);
  }, [totals]);

  useEffect(() => {
    setLiveEvents(events);
  }, [events]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const streamUrl = `${apiBaseUrl.replace(/\/$/, '')}/stream`;
    const eventSource = new EventSource(streamUrl);
    eventSource.addEventListener('ledger', (evt) => {
      try {
        const payload = JSON.parse((evt as MessageEvent).data) as LedgerStreamPayload;
        setLiveTotals(payload.totals);
        setLiveEvents((current) => {
          const filtered = current.filter((item) => item.id !== payload.entry.id);
          return [payload.entry, ...filtered].slice(0, 50);
        });
      } catch (error) {
        console.error('Unable to parse ledger stream payload', error);
      }
    });
    eventSource.onerror = (error) => {
      console.warn('Ledger stream error', error);
    };
    return () => {
      eventSource.close();
    };
  }, [apiBaseUrl]);

  return (
    <>
      <Head>
        <title>Little Footsteps Transparency Ledger</title>
        <meta name="description" content="Transparency dashboard for the Little Footsteps childcare commons bank." />
      </Head>
      <main style={{ maxWidth: '64rem', margin: '0 auto', padding: '3rem 1.5rem' }}>
        <section style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, margin: 0 }}>Little Footsteps Transparency Ledger</h1>
          <p style={{ color: '#475569', marginTop: '0.75rem', fontSize: '1rem', maxWidth: '50rem' }}>
            Every donation, childcare credit, and impact payout is recorded against the Postgres-backed transparency ledger.
            Verifiable credentials are issued with our did:web anchor so families and regulators can audit flows in real time.
          </p>
          <p style={{ color: '#64748b', marginTop: '0.5rem', fontSize: '0.9rem' }}>Data refreshed at {new Date(generatedAt).toLocaleString()} from {apiBaseUrl}.</p>
        </section>

        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2.5rem' }}>
          <StatCard label="Today's Inflows" value={formatCurrency(liveTotals.inflows, 'USD')} />
          <StatCard label="Today's Outflows" value={formatCurrency(liveTotals.outflows, 'USD')} />
          <StatCard label="Net Position" value={formatCurrency(liveTotals.net, 'USD')} />
        </section>

        <section style={{ marginBottom: '1.5rem' }}>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 600, margin: 0 }}>Latest Activity</h2>
            <small style={{ color: '#64748b' }}>Showing the 50 most recent ledger events.</small>
          </header>
          <div style={{ marginTop: '1.5rem', display: 'grid', gap: '1rem' }}>
            {liveEvents.length === 0 && (
              <p style={{ color: '#64748b' }}>
                No ledger events yet. When the issuer logs a donation or payout via the API, it will appear here automatically.
              </p>
            )}
            {liveEvents.map((event) => (
              <article key={event.id} className="card">
                <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className={event.direction === 'INFLOW' ? 'badge-inflow' : 'badge-outflow'}>
                    {event.direction}
                  </span>
                  <time style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {new Date(event.occurred_at).toLocaleString()}
                  </time>
                </header>
                <div style={{ marginTop: '0.75rem', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    {event.direction === 'INFLOW' ? (
                      <p style={{ margin: '0 0 0.35rem 0', color: '#334155', fontSize: '0.95rem' }}>
                        Source: {event.source ?? 'Community Pool'}
                      </p>
                    ) : (
                      <p style={{ margin: '0 0 0.35rem 0', color: '#334155', fontSize: '0.95rem' }}>
                        Purpose: {event.purpose ?? 'Unspecified distribution'}
                      </p>
                    )}
                    {event.narrative && (
                      <p style={{ margin: '0 0 0.35rem 0', color: '#475569', fontSize: '0.85rem' }}>
                        Narrative: {event.narrative}
                      </p>
                    )}
                    {event.beneficiary && (
                      <p style={{ margin: '0 0 0.35rem 0', color: '#334155', fontSize: '0.9rem' }}>
                        Beneficiary: {event.beneficiary}
                      </p>
                    )}
                    {event.tags && event.tags.length > 0 && (
                      <div style={{ marginTop: '0.35rem' }}>
                        {event.tags.map((tag) => (
                          <span key={tag} className="tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>
                    {formatCurrency(event.amount_cents, event.currency)}
                  </span>
                </div>
                {event.vc_id && (
                  <div style={{ marginTop: '0.75rem' }}>
                    <Link href={`${trustRegistryUrl.replace(/\/$/, '')}/vc/${event.vc_id}`}>
                      View verifiable credential
                    </Link>
                  </div>
                )}
                {(event.proof_path || event.ots_receipt) && (
                  <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#475569' }}>
                    {event.proof_path && (
                      <div>Proof bundle: <code>{event.proof_path}</code></div>
                    )}
                    {event.ots_receipt && (
                      <div>OTS receipt: <code>{event.ots_receipt}</code></div>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>

        <section className="card">
          <h3 style={{ marginTop: 0 }}>Trust Registry</h3>
          <p style={{ color: '#475569', fontSize: '0.95rem' }}>
            Credential verification policies live in the Little Footsteps trust registry. Keep it up to date as new programs roll out.
          </p>
          <Link href={trustRegistryUrl} target="_blank" rel="noreferrer">
            View trust registry JSON
          </Link>
        </section>

        <GovernanceSection amendments={governance} />

        <AuditTrailSection audit={audit} />
      </main>
    </>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p style={{ color: '#64748b', fontSize: '0.85rem', margin: 0 }}>{label}</p>
      <p style={{ fontWeight: 600, fontSize: '1.75rem', margin: '0.5rem 0 0 0' }}>{value}</p>
    </div>
  );
}

function GovernanceSection({ amendments }: { amendments: GovernanceAmendment[] }) {
  if (!amendments || amendments.length === 0) {
    return (
      <section className="card">
        <h3 style={{ marginTop: 0 }}>Governance Amendments</h3>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
          No published amendments yet. Once the Echo sovereign assembly ratifies updates they will be listed here.
        </p>
      </section>
    );
  }

  return (
    <section className="card">
      <h3 style={{ marginTop: 0 }}>Governance Amendments</h3>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '1rem' }}>
        {amendments.map((amendment) => (
          <li key={amendment.id} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <strong style={{ fontSize: '1.05rem' }}>{amendment.title}</strong>
              <time style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                Adopted {new Date(amendment.adopted_at).toLocaleString()}
              </time>
            </div>
            <p style={{ margin: '0.5rem 0', color: '#475569', fontSize: '0.9rem' }}>{amendment.summary}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', fontSize: '0.75rem', color: '#64748b' }}>
              {amendment.status && <span className="tag">Status: {amendment.status}</span>}
              {amendment.ratified_by && amendment.ratified_by.map((actor) => (
                <span key={actor} className="tag">Ratified by {actor}</span>
              ))}
            </div>
            {amendment.proof_uri && (
              <div style={{ marginTop: '0.5rem' }}>
                <a href={amendment.proof_uri} target="_blank" rel="noreferrer">
                  View proof bundle
                </a>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function AuditTrailSection({ audit }: { audit: AuditTrail }) {
  const ledgerItems = audit?.ledger ?? [];
  const continuityItems = audit?.continuity ?? [];

  return (
    <section className="card">
      <h3 style={{ marginTop: 0 }}>Audit Trail</h3>
      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div>
          <h4 style={{ margin: '0 0 0.5rem 0' }}>Ledger Proofs</h4>
          {ledgerItems.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No ledger entries recorded yet.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.75rem' }}>
              {ledgerItems.map((item) => (
                <li key={`ledger-${item.seq ?? item.digest}`} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.85rem', color: '#334155' }}>
                    <strong>Seq {item.seq ?? 'n/a'}</strong> · {item.direction ?? '—'} {item.amount ?? ''} {item.asset ?? ''}
                  </div>
                  {item.timestamp && (
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Timestamp: {new Date(item.timestamp).toLocaleString()}</div>
                  )}
                  {item.digest && (
                    <div style={{ fontSize: '0.75rem', color: '#475569' }}>Digest: <code>{item.digest}</code></div>
                  )}
                  {item.proof_path && (
                    <div style={{ fontSize: '0.75rem', color: '#475569' }}>Proof: <code>{item.proof_path}</code></div>
                  )}
                  {item.ots_receipt && (
                    <div style={{ fontSize: '0.75rem', color: '#475569' }}>OTS: <code>{item.ots_receipt}</code></div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <h4 style={{ margin: '0 0 0.5rem 0' }}>Continuity Checkpoints</h4>
          {continuityItems.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No multi-sig recovery checkpoints published yet.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.75rem' }}>
              {continuityItems.map((checkpoint, idx) => (
                <li key={`checkpoint-${checkpoint.seq ?? idx}`} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.85rem', color: '#334155' }}>
                    <strong>Threshold {checkpoint.threshold}-of-{checkpoint.trustees.length}</strong>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Published {new Date(checkpoint.timestamp).toLocaleString()}</div>
                  {checkpoint.digest && (
                    <div style={{ fontSize: '0.75rem', color: '#475569' }}>Digest: <code>{checkpoint.digest}</code></div>
                  )}
                  {checkpoint.trustees.length > 0 && (
                    <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                      Trustees: {checkpoint.trustees.join(', ')}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
