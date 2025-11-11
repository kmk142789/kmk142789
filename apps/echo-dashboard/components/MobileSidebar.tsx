'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppContext } from './AppContext';
import { NAV_ITEMS } from './SiteNav';
import { cn } from '@/lib/utils';

export default function MobileSidebar() {
  const pathname = usePathname();
  const { sidebarOpen, closeSidebar } = useAppContext();

  if (!sidebarOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex lg:hidden" role="dialog" aria-modal="true">
      <div
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
        onClick={closeSidebar}
        role="presentation"
      />
      <aside className="relative ml-auto flex h-full w-72 flex-col border-l border-slate-800 bg-slate-950/95 p-6 shadow-xl">
        <header className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-[0.35em] text-echo-ember">
            Echo Navigation
          </span>
          <button
            type="button"
            onClick={closeSidebar}
            className="rounded-md border border-slate-700 px-3 py-1 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Close
          </button>
        </header>
        <nav className="mt-6 flex flex-1 flex-col gap-2 text-sm">
          <ul className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={closeSidebar}
                    className={cn(
                      'block rounded-md px-3 py-2 transition',
                      isActive
                        ? 'bg-echo-ember/20 text-echo-ember shadow-sm'
                        : 'text-slate-200 hover:bg-slate-900/70 hover:text-white',
                    )}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
          <div className="mt-auto rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-xs text-slate-400">
            Toggle panels and rituals even while on the move. Configure Neon storage and Codex rituals from any orbit.
          </div>
        </nav>
      </aside>
    </div>
  );
}

