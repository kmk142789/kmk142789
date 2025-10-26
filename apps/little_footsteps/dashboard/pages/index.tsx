import Head from 'next/head';
import Link from 'next/link';
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
}

export const getServerSideProps: GetServerSideProps<DashboardProps> = async () => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:4000';
  const totalsUrl = `${baseUrl}/metrics/totals`;
  const eventsUrl = `${baseUrl}/ledger/events?limit=50`;

  let totals = { inflows: 0, outflows: 0, net: 0 };
  let events: LedgerEvent[] = [];

  try {
    const [totalsRes, eventsRes] = await Promise.all([
      fetch(totalsUrl),
      fetch(eventsUrl),
    ]);

    if (totalsRes.ok) {
      totals = await totalsRes.json();
    }

    if (eventsRes.ok) {
      events = await eventsRes.json();
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

export default function DashboardPage({ totals, events, apiBaseUrl, generatedAt }: InferGetServerSidePropsType<typeof getServerSideProps>) {
  const trustRegistryUrl = process.env.NEXT_PUBLIC_TRUST_REGISTRY_URL ?? 'https://kmk142789.github.io/little-footsteps-bank/trust-registry.json';

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
          <StatCard label="Today's Inflows" value={formatCurrency(totals.inflows, 'USD')} />
          <StatCard label="Today's Outflows" value={formatCurrency(totals.outflows, 'USD')} />
          <StatCard label="Net Position" value={formatCurrency(totals.net, 'USD')} />
        </section>

        <section style={{ marginBottom: '1.5rem' }}>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 600, margin: 0 }}>Latest Activity</h2>
            <small style={{ color: '#64748b' }}>Showing the 50 most recent ledger events.</small>
          </header>
          <div style={{ marginTop: '1.5rem', display: 'grid', gap: '1rem' }}>
            {events.length === 0 && (
              <p style={{ color: '#64748b' }}>
                No ledger events yet. When the issuer logs a donation or payout via the API, it will appear here automatically.
              </p>
            )}
            {events.map((event) => (
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
