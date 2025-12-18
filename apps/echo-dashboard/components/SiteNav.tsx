'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppContext } from './AppContext';

export const NAV_ITEMS = [
  { href: '/', label: 'Pulse' },
  { href: '/codex', label: 'Codex' },
  { href: '/assistant', label: 'Assistant' },
  { href: '/emotional-archaeology', label: 'Emotional Archaeology' },
  { href: '/wallets', label: 'Wallets' },
];

export default function SiteNav() {
  const pathname = usePathname();
  const { toggleSidebar } = useAppContext();

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleSidebar}
            className="inline-flex items-center rounded-md border border-slate-700 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-slate-300 transition hover:border-slate-500 hover:text-white focus:outline-none focus:ring-2 focus:ring-echo-ember/60 lg:hidden"
            aria-label="Open navigation menu"
          >
            Menu
          </button>
          <div className="text-sm font-semibold uppercase tracking-widest text-echo-ember">
            Echo Pulse Dashboard
          </div>
        </div>
        <ul className="hidden items-center gap-4 text-sm text-slate-300 lg:flex">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`rounded-md px-3 py-2 transition ${
                    isActive
                      ? 'bg-echo-ember/20 text-echo-ember'
                      : 'hover:bg-slate-900/70 hover:text-white'
                  }`}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
