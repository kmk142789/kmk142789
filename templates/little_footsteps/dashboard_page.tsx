import { GetServerSideProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';

interface LedgerEvent {
  id: string;
  direction: 'INFLOW' | 'OUTFLOW';
  amount_cents: number;
  currency: string;
  purpose?: string;
  source?: string;
  occurred_at: string;
  vc_id?: string;
  tags?: string[];
  beneficiary?: string;
}

interface DashboardProps {
  totals: {
    inflows: number;
    outflows: number;
    net: number;
  };
  events: LedgerEvent[];
}

export const getServerSideProps: GetServerSideProps<DashboardProps> = async () => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const [totalsRes, eventsRes] = await Promise.all([
    fetch(`${baseUrl}/metrics/totals`),
    fetch(`${baseUrl}/ledger/events?limit=50`),
  ]);

  const totals = await totalsRes.json();
  const events = await eventsRes.json();

  return { props: { totals, events } };
};

function formatCurrency(cents: number, currency: string) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(cents / 100);
}

const DashboardPage = ({ totals, events }: DashboardProps) => {
  return (
    <>
      <Head>
        <title>Little Footsteps Transparency Ledger</title>
      </Head>
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        <section>
          <h1 className="text-3xl font-bold">Little Footsteps Transparency Ledger</h1>
          <p className="text-gray-600 mt-2">
            Track every donation and impact payout in real time. Donor identities remain private by default.
          </p>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Today's Inflows" value={formatCurrency(totals.inflows, 'USD')} />
          <StatCard label="Today's Outflows" value={formatCurrency(totals.outflows, 'USD')} />
          <StatCard label="Net Position" value={formatCurrency(totals.net, 'USD')} />
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">Latest Activity</h2>
          <div className="space-y-4">
            {events.map((event) => (
              <article key={event.id} className="border border-gray-200 rounded-lg p-4">
                <header className="flex justify-between items-center">
                  <span className={`text-sm font-semibold ${event.direction === 'INFLOW' ? 'text-green-600' : 'text-blue-600'}`}>
                    {event.direction}
                  </span>
                  <time className="text-xs text-gray-500">
                    {new Date(event.occurred_at).toLocaleString()}
                  </time>
                </header>
                <div className="mt-2 flex justify-between">
                  <div>
                    {event.direction === 'INFLOW' ? (
                      <p className="text-sm text-gray-700">Source: {event.source ?? 'N/A'}</p>
                    ) : (
                      <p className="text-sm text-gray-700">Purpose: {event.purpose ?? 'Unspecified'}</p>
                    )}
                    {event.beneficiary && (
                      <p className="text-sm text-gray-700">Beneficiary: {event.beneficiary}</p>
                    )}
                    {event.tags && (
                      <p className="text-xs text-gray-500">Tags: {event.tags.join(', ')}</p>
                    )}
                  </div>
                  <span className="text-lg font-semibold">
                    {formatCurrency(event.amount_cents, event.currency)}
                  </span>
                </div>
                {event.vc_id && (
                  <div className="mt-3">
                    <Link href={`${process.env.NEXT_PUBLIC_TRUST_REGISTRY_URL}/vc/${event.vc_id}`} className="text-sm text-indigo-600 hover:underline">
                      View verifiable credential
                    </Link>
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      </main>
    </>
  );
};

const StatCard = ({ label, value }: { label: string; value: string }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <p className="text-sm text-gray-500">{label}</p>
    <p className="text-2xl font-semibold mt-1">{value}</p>
  </div>
);

export default DashboardPage;
