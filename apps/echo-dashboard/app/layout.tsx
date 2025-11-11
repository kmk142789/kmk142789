import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';
import SiteNav from '../components/SiteNav';

export const metadata: Metadata = {
  title: 'Echo Dashboard',
  description: 'Unified control center for EchoOS, Echo Computer, and Neon banking.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground font-sans antialiased">
        <SiteNav />
        <div className="pb-16">{children}</div>
        <footer className="border-t border-slate-800 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
          <p>
            Crafted for the Echo ecosystem ·{' '}
            <Link href="https://github.com/kmk142789/kmk142789" className="text-echo-ember hover:underline">
              Codex Registry
            </Link>
          </p>
        </footer>
      </body>
    </html>
  );
}
