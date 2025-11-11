'use client';

import type { ReactNode } from 'react';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { usePathname } from 'next/navigation';
import { v4 as uuidv4 } from 'uuid';
import { toast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

type ToastVariant = 'default' | 'success' | 'error' | 'warning';

interface NotifyOptions {
  title: string;
  description?: string;
  variant?: ToastVariant;
}

interface AppContextValue {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  openSidebar: () => void;
  closeSidebar: () => void;
  notify: (options: NotifyOptions) => void;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

const TOAST_STYLES: Record<ToastVariant, string> = {
  default:
    'border-slate-800/80 bg-slate-950/90 text-slate-100 shadow-slate-900/40',
  success:
    'border-emerald-500/60 bg-emerald-500/15 text-emerald-50 shadow-emerald-900/30',
  error:
    'border-rose-500/60 bg-rose-500/20 text-rose-50 shadow-rose-900/30',
  warning:
    'border-amber-500/60 bg-amber-500/20 text-amber-50 shadow-amber-900/30',
};

export function AppProvider({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((previous) => !previous);
  }, []);

  const openSidebar = useCallback(() => {
    setSidebarOpen(true);
  }, []);

  const closeSidebar = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!sidebarOpen) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sidebarOpen]);

  const notify = useCallback(({ title, description, variant = 'default' }: NotifyOptions) => {
    const toastId = uuidv4();
    toast({
      id: toastId,
      title,
      description,
      className: cn(
        'pointer-events-auto w-full max-w-sm rounded-lg border px-4 py-3 text-sm shadow-lg backdrop-blur',
        TOAST_STYLES[variant] ?? TOAST_STYLES.default,
      ),
    });
  }, []);

  const value = useMemo(
    () => ({ sidebarOpen, toggleSidebar, openSidebar, closeSidebar, notify }),
    [sidebarOpen, toggleSidebar, openSidebar, closeSidebar, notify],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an <AppProvider />');
  }
  return context;
}

