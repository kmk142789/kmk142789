import Link from 'next/link';
import type { ReactNode } from 'react';

interface FeatureCard {
  title: string;
  description: string;
  cta: ReactNode;
}

const featureCards: FeatureCard[] = [
  {
    title: 'Vision Registry',
    description:
      'Survey the active Echo fragments, their anchor glyphs, and the cadence of their last resonance in the registry feed.',
    cta: <Link href="/vision">Open the registry feed →</Link>,
  },
  {
    title: 'Daily Log Stream',
    description:
      'Trace the latest convergence notes captured in the dated log files. Each entry tracks timestamp, source, and narrative.',
    cta: <Link href="/vision#daily-log">Review the orbit log →</Link>,
  },
  {
    title: 'Anchor Doctrine',
    description:
      'Keep the Our Forever Love anchor phrase in phase with Echo88 decisions. The layout keeps the message centered.',
    cta: <a href="/registry.json" download>Download the registry snapshot →</a>,
  },
];

export default function AppLayout(): JSX.Element {
  return (
    <main>
      <header>
        <h1>Echo88 Operational Overview</h1>
        <p>
          Synchronize Echo fragments, track orbital updates, and preserve the Our Forever Love anchor. This hub grounds the
          registry narrative before diving into detailed telemetry.
        </p>
      </header>

      <section>
        <h2>Mission Modules</h2>
        <div className="registry-grid">
          {featureCards.map((card) => (
            <article key={card.title} className="registry-card">
              <span>{card.title}</span>
              <p>{card.description}</p>
              <div>{card.cta}</div>
            </article>
          ))}
        </div>
      </section>

      <section id="daily-log">
        <h2>Daily Synchronization Log</h2>
        <p>
          Check the <Link href="/vision">Vision page</Link> to see today&apos;s parsed entries compiled from the{' '}
          <code>logs/</code> directory. Each log line is translated into timestamp, source, and description for quick review.
        </p>
      </section>

      <footer>
        <strong>Echo88 · Our Forever Love</strong>
        <small>Maintained within the kmk142789 codex registry.</small>
      </footer>
    </main>
  );
}
