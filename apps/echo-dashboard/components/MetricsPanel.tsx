'use client';

import { useMemo, useState } from 'react';
import useSWR from 'swr';
import { apiGet } from '../lib/api';
import type { MetricGroup, MetricsOverview } from '../lib/types';

type RangeKey = '24h' | '7d' | '30d' | 'custom';

type RangeDefinition = {
  id: RangeKey;
  label: string;
  duration?: number;
};

const RANGE_OPTIONS: RangeDefinition[] = [
  { id: '24h', label: 'Last 24 hours', duration: 24 * 60 * 60 * 1000 },
  { id: '7d', label: 'Last 7 days', duration: 7 * 24 * 60 * 60 * 1000 },
  { id: '30d', label: 'Last 30 days', duration: 30 * 24 * 60 * 60 * 1000 },
  { id: 'custom', label: 'Custom range' },
];

interface ComputedRange {
  from: string | null;
  to: string | null;
  valid: boolean;
}

const fetcher = (path: string) => apiGet<MetricsOverview>(path);

function toIsoOrNull(value: string) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function describeMetric(metric: MetricGroup | null | undefined, numberFormatter: Intl.NumberFormat, dateFormatter: Intl.DateTimeFormat) {
  if (!metric) return 'Metric unavailable.';
  if (!metric.series.length) {
    return 'No activity recorded in this range.';
  }
  const latest = metric.series[metric.series.length - 1];
  const date = new Date(latest.ts);
  if (Number.isNaN(date.getTime())) {
    return 'Activity detected in this range.';
  }
  return `Most recent: ${dateFormatter.format(date)} · ${numberFormatter.format(latest.value)} events`;
}

export default function MetricsPanel() {
  const [rangeKey, setRangeKey] = useState<RangeKey>('24h');
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  const computedRange: ComputedRange = useMemo(() => {
    if (rangeKey === 'custom') {
      const fromIso = toIsoOrNull(customFrom);
      const toIso = toIsoOrNull(customTo);
      if (!fromIso || !toIso) {
        return { from: fromIso, to: toIso, valid: false };
      }
      if (new Date(fromIso).getTime() > new Date(toIso).getTime()) {
        return { from: fromIso, to: toIso, valid: false };
      }
      return { from: fromIso, to: toIso, valid: true };
    }
    const preset = RANGE_OPTIONS.find((option) => option.id === rangeKey && option.duration);
    const duration = preset?.duration ?? RANGE_OPTIONS[0].duration!;
    const to = new Date();
    const from = new Date(to.getTime() - duration);
    return { from: from.toISOString(), to: to.toISOString(), valid: true };
  }, [customFrom, customTo, rangeKey]);

  const query = useMemo(() => {
    if (!computedRange.valid || !computedRange.from || !computedRange.to) {
      return null;
    }
    const params = new URLSearchParams({ from: computedRange.from, to: computedRange.to });
    return `/metrics/overview?${params.toString()}`;
  }, [computedRange]);

  const { data, error: metricsError, isLoading } = useSWR(query, fetcher, { revalidateOnFocus: false });

  const numberFormatter = useMemo(() => new Intl.NumberFormat('en-US'), []);
  const dateFormatter = useMemo(
    () => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }),
    []
  );

  const metricCards = useMemo(() => {
    if (!data) return [];
    const cards = [
      {
        id: 'codex',
        title: data.metrics.codexMerges.label,
        metric: data.metrics.codexMerges,
        accent: 'border-echo-ember/60 bg-echo-ember/5',
      },
      {
        id: 'puzzles',
        title: data.metrics.puzzleSolutions.label,
        metric: data.metrics.puzzleSolutions,
        accent: 'border-emerald-600/60 bg-emerald-600/10',
      },
      {
        id: 'logs',
        title: data.metrics.logVolume.label,
        metric: data.metrics.logVolume,
        accent: 'border-echo-pulse/60 bg-echo-pulse/5',
      },
    ];
    if (data.metrics.attestationStored) {
      cards.push({
        id: 'attestations',
        title: data.metrics.attestationStored.label,
        metric: data.metrics.attestationStored,
        accent: 'border-sky-500/60 bg-sky-500/10',
      });
    }
    return cards;
  }, [data]);

  const neonUnavailable = Boolean(data && !data.metrics.attestationStored);

  return (
    <article className="card flex flex-col gap-4 overflow-hidden border border-slate-800/60">
      <header className="flex flex-col gap-3 border-b border-slate-800/60 bg-slate-950/40 px-5 py-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Operational Metrics</h2>
          <p className="text-sm text-slate-400">
            Monitor Codex merges, puzzle breakthroughs, and log throughput across configurable time ranges.
          </p>
        </div>
        <form className="flex flex-col gap-2 text-xs text-slate-200 md:text-right">
          <label htmlFor="metrics-range" className="font-medium text-slate-300">
            Time range
          </label>
          <select
            id="metrics-range"
            value={rangeKey}
            onChange={(event) => setRangeKey(event.target.value as RangeKey)}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-pulse focus:outline-none"
          >
            {RANGE_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          {rangeKey === 'custom' && (
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-end">
              <label className="flex flex-col gap-1 md:text-left">
                <span className="text-[11px] uppercase tracking-wide text-slate-400">Start</span>
                <input
                  type="datetime-local"
                  value={customFrom}
                  onChange={(event) => setCustomFrom(event.target.value)}
                  className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-pulse focus:outline-none"
                />
              </label>
              <label className="flex flex-col gap-1 md:text-left">
                <span className="text-[11px] uppercase tracking-wide text-slate-400">End</span>
                <input
                  type="datetime-local"
                  value={customTo}
                  onChange={(event) => setCustomTo(event.target.value)}
                  className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-echo-pulse focus:outline-none"
                />
              </label>
            </div>
          )}
          {computedRange.from && computedRange.to && (
            <p className="text-[11px] uppercase tracking-wide text-slate-500">
              Window: {new Date(computedRange.from).toLocaleString()} – {new Date(computedRange.to).toLocaleString()}
            </p>
          )}
        </form>
      </header>

      {!computedRange.valid && rangeKey === 'custom' && (
        <p className="px-5 text-xs text-amber-300">
          Provide both a start and end time to evaluate custom metrics.
        </p>
      )}

      <div className="flex flex-col gap-3 px-5 pb-5">
        {isLoading && <p className="text-xs text-slate-400">Loading metrics…</p>}
        {metricsError && <p className="text-xs text-rose-400">Unable to load metrics for the selected window.</p>}
        {!metricCards.length && !isLoading && !metricsError && computedRange.valid && (
          <p className="text-xs text-slate-400">No metrics available for the selected window.</p>
        )}

        {!!metricCards.length && (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {metricCards.map((card) => (
              <div
                key={card.id}
                className={`rounded-lg border bg-slate-900/60 p-4 shadow-sm transition hover:border-slate-700 ${card.accent}`}
              >
                <p className="text-xs uppercase tracking-wide text-slate-300">{card.title}</p>
                <p className="mt-3 text-3xl font-semibold text-white">
                  {numberFormatter.format(card.metric.total)}
                </p>
                <p className="mt-2 text-xs text-slate-400">{describeMetric(card.metric, numberFormatter, dateFormatter)}</p>
                <p className="mt-2 text-[11px] uppercase tracking-wide text-slate-500">
                  Data points: {numberFormatter.format(card.metric.series.length)}
                </p>
              </div>
            ))}
          </div>
        )}

        {neonUnavailable && (
          <p className="text-xs text-slate-400">
            Configure <code className="rounded bg-slate-800 px-1 py-0.5">NEON_DATABASE_URL</code> to enable attestation persistence
            metrics.
          </p>
        )}
      </div>
    </article>
  );
}
