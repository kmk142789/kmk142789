'use client';

import { useCallback } from 'react';
import useSWR from 'swr';
import SettingsScreen from '@/components/SettingsScreen';
import { useAppContext } from '@/components/AppContext';
import { apiGet, apiPut } from '@/lib/api';
import type { Policy } from '@/lib/types';

interface PolicyResponse {
  policy: Policy;
}

const fetchPolicy = async () => apiGet<PolicyResponse>('/whispervault/policy');

export default function SettingsPage() {
  const { notify } = useAppContext();
  const { data, error, isLoading, mutate } = useSWR<PolicyResponse>('/whispervault/policy', fetchPolicy, {
    refreshInterval: 60000,
    revalidateOnFocus: false,
  });

  const handleUpdate = useCallback(
    async (updated: Policy) => {
      try {
        const response = await apiPut<PolicyResponse>('/whispervault/policy', updated);
        await mutate(response, { revalidate: false });
        notify({
          title: 'Policy updated',
          description: 'WhisperVault thresholds saved to the steward ledger.',
          variant: 'success',
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to update policy.';
        notify({
          title: 'Failed to update policy',
          description: message,
          variant: 'error',
        });
        throw err instanceof Error ? err : new Error(message);
      }
    },
    [mutate, notify],
  );

  if (error) {
    return (
      <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-10">
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-6 text-rose-100">
          <h1 className="text-xl font-semibold">Policy feed unavailable</h1>
          <p className="mt-2 text-sm opacity-80">
            {error instanceof Error
              ? error.message
              : 'Unable to load WhisperVault steward policy from the backend API.'}
          </p>
        </div>
      </main>
    );
  }

  if (isLoading || !data) {
    return (
      <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-10">
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-6 text-slate-300">
          <h1 className="text-xl font-semibold text-white">Loading steward policy…</h1>
          <p className="mt-2 text-sm text-slate-400">
            Synchronising WhisperVault thresholds from the policy ledger.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <SettingsScreen policy={data.policy} onUpdatePolicy={handleUpdate} />
    </main>
  );
}
