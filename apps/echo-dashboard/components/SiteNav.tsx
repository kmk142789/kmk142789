'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/', label: 'Pulse' },
  { href: '/codex', label: 'Codex' },
  { href: '/assistant', label: 'Assistant' },
];

export default function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="text-sm font-semibold uppercase tracking-widest text-echo-ember">Echo Pulse Dashboard</div>
        <ul className="flex items-center gap-4 text-sm text-slate-300">
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
