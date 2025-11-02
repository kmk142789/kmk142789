'use client';

import { useMemo, useState } from 'react';
import useSWR from 'swr';
import { apiGet } from '../lib/api';
import type { CodexRegistryResponse, CodexItem } from '../lib/types';

const fetcher = async (path: string) => apiGet<CodexRegistryResponse>(path);

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
}

export default function CodexTimeline() {
  const { data, error } = useSWR('/api/codex', fetcher);
  const [selectedLabel, setSelectedLabel] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');

  const labels = useMemo(() => {
    const unique = new Set<string>();
    (data?.items ?? []).forEach((item) => item.labels.forEach((label) => unique.add(label)));
    return Array.from(unique).sort();
  }, [data]);

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((item) => {
      const matchesLabel = !selectedLabel || item.labels.includes(selectedLabel);
      const matchesDate = !fromDate || new Date(item.merged_at) >= new Date(fromDate);
      return matchesLabel && matchesDate;
    });
  }, [data, selectedLabel, fromDate]);

  if (error) {
    return <p className="text-sm text-rose-400">Unable to load Codex registry.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="badge text-echo-ember">Echo Codex</p>
          <h1 className="text-3xl font-semibold text-white">Registry Timeline</h1>
          <p className="text-slate-300">Filter merged pull requests by label and timestamp.</p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          <label className="flex flex-col gap-1 text-slate-300">
            Label
            <select
              value={selectedLabel}
              onChange={(event) => setSelectedLabel(event.target.value)}
              className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-white"
            >
              <option value="">All labels</option>
              {labels.map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-slate-300">
            From date
            <input
              type="date"
              value={fromDate}
              onChange={(event) => setFromDate(event.target.value)}
              className="rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-white"
            />
          </label>
        </div>
      </header>

      <section className="rounded-xl border border-slate-800 bg-slate-950/60 p-6">
        <ol className="relative flex flex-col gap-6 border-l border-slate-800 pl-6">
          {filtered.map((item: CodexItem) => (
            <li key={item.id} className="space-y-2">
              <span className="absolute -left-2 mt-1 h-3 w-3 rounded-full border border-echo-ember bg-echo-ember/40" aria-hidden />
              <p className="text-xs uppercase tracking-wide text-slate-400">{formatDate(item.merged_at)}</p>
              <div className="flex flex-col gap-1">
                <a href={item.url} target="_blank" rel="noreferrer" className="text-lg font-semibold text-white hover:text-echo-ember">
                  #{item.id} · {item.title}
                </a>
                <p className="text-sm text-slate-300">{item.summary}</p>
                <p className="text-xs text-slate-400">Tags: {item.labels.join(', ') || 'untagged'} · Commit {item.hash}</p>
              </div>
            </li>
          ))}
          {!filtered.length && (
            <li className="text-sm text-slate-500">No entries match the current filters.</li>
          )}
        </ol>
      </section>
    </div>
  );
}
