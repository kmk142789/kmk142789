'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiGet } from '../lib/api';
import type { LogChunkDescriptor } from '../lib/types';

interface Props {
  files: string[];
  error: string | null;
  selected: string | null;
  onSelect: (name: string) => void;
}

const CHUNK_BYTES = 8192;
const FOLLOW_INTERVAL_MS = 4000;

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes)) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unitIndex = -1;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 || unitIndex === -1 ? 0 : 1)} ${units[Math.max(unitIndex, 0)]}`;
}

export default function LogsPanel({ files, error, selected, onSelect }: Props) {
  const sortedFiles = useMemo(() => [...files].sort().reverse(), [files]);
  const [chunks, setChunks] = useState<LogChunkDescriptor[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [loadingNewer, setLoadingNewer] = useState(false);
  const [follow, setFollow] = useState(false);
  const scrollRef = useRef<HTMLPreElement>(null);
  const shouldAutoScrollRef = useRef(false);
  const followRef = useRef(false);
  const numberFormatter = useMemo(() => new Intl.NumberFormat('en-US'), []);

  const combinedLog = useMemo(() => chunks.map((entry) => entry.chunk).join(''), [chunks]);
  const firstChunk = chunks[0] ?? null;
  const lastChunk = chunks[chunks.length - 1] ?? null;
  const totalSize = lastChunk?.size ?? 0;
  const loadedStart = firstChunk?.start ?? 0;
  const loadedEnd = lastChunk?.end ?? 0;

  const fetchChunk = useCallback(
    async (params: { cursor?: string | number; direction?: 'forward' | 'backward' }) => {
      if (!selected) {
        throw new Error('no_file_selected');
      }
      const search = new URLSearchParams();
      search.set('limit', String(CHUNK_BYTES));
      if (params.cursor !== undefined) {
        search.set('cursor', String(params.cursor));
      }
      if (params.direction) {
        search.set('direction', params.direction);
      }
      const path = `/logs/${encodeURIComponent(selected)}/chunk?${search.toString()}`;
      return apiGet<LogChunkDescriptor>(path);
    },
    [selected]
  );

  const loadLatest = useCallback(async () => {
    if (!selected) return;
    setLoadingLatest(true);
    setStreamError(null);
    shouldAutoScrollRef.current = true;
    try {
      const chunk = await fetchChunk({ cursor: 'latest' });
      setChunks(chunk ? [chunk] : []);
    } catch (err) {
      console.error('Unable to load latest log chunk', err);
      setChunks([]);
      setStreamError('Failed to stream log file.');
    } finally {
      setLoadingLatest(false);
    }
  }, [fetchChunk, selected]);

  const loadOlder = useCallback(async () => {
    if (!selected || !firstChunk?.hasMoreBackward) return;
    setLoadingOlder(true);
    setStreamError(null);
    try {
      const cursor = firstChunk.previousCursor ?? firstChunk.start;
      const chunk = await fetchChunk({ cursor, direction: 'backward' });
      setChunks((prev) => [chunk, ...prev]);
    } catch (err) {
      console.error('Unable to load older log chunk', err);
      setStreamError('Failed to load older log entries.');
    } finally {
      setLoadingOlder(false);
    }
  }, [fetchChunk, firstChunk, selected]);

  const loadNewer = useCallback(async () => {
    if (!selected || !lastChunk) return;
    setLoadingNewer(true);
    setStreamError(null);
    try {
      const cursor = lastChunk.nextCursor ?? lastChunk.end;
      const chunk = await fetchChunk({ cursor, direction: 'forward' });
      setChunks((prev) => {
        if (!chunk.chunk) {
          return prev.map((entry, index) =>
            index === prev.length - 1
              ? {
                  ...entry,
                  end: chunk.end,
                  size: chunk.size,
                  hasMoreForward: chunk.hasMoreForward,
                  nextCursor: chunk.nextCursor,
                }
              : entry
          );
        }
        return [...prev, chunk];
      });
      if (followRef.current) {
        shouldAutoScrollRef.current = true;
      }
    } catch (err) {
      console.error('Unable to load newer log chunk', err);
      setStreamError('Failed to load newer log entries.');
    } finally {
      setLoadingNewer(false);
    }
  }, [fetchChunk, lastChunk, selected]);

  useEffect(() => {
    followRef.current = follow;
    if (follow) {
      shouldAutoScrollRef.current = true;
    }
  }, [follow]);

  useEffect(() => {
    setChunks([]);
    setStreamError(null);
    setFollow(false);
    if (selected) {
      void loadLatest();
    }
  }, [loadLatest, selected]);

  useEffect(() => {
    if (!follow || !selected) return undefined;
    const interval = setInterval(() => {
      void loadNewer();
    }, FOLLOW_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [follow, loadNewer, selected]);

  useEffect(() => {
    if (!chunks.length) return;
    if (!(followRef.current || shouldAutoScrollRef.current)) return;
    const container = scrollRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
    shouldAutoScrollRef.current = false;
  }, [chunks]);

  const handleSelect = useCallback(
    (file: string) => {
      if (file === selected) return;
      onSelect(file);
    },
    [onSelect, selected]
  );

  const handleFollowToggle = useCallback(() => {
    setFollow((value) => !value);
  }, []);

  return (
    <article className="card flex flex-col overflow-hidden">
      <header className="flex flex-col gap-2 border-b border-slate-800 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Echo Computer Logs</h2>
          <p className="text-sm text-slate-400">
            Stream Echo telemetry with incremental pagination and real-time following.
          </p>
        </div>
        {selected && lastChunk && (
          <div className="text-xs text-slate-400">
            <p>
              Loaded {numberFormatter.format(loadedEnd - loadedStart)} bytes · Window {numberFormatter.format(loadedStart)} –{' '}
              {numberFormatter.format(loadedEnd)} of {formatBytes(totalSize)}
            </p>
          </div>
        )}
      </header>
      <div className="flex flex-1 flex-col gap-4 p-5 md:flex-row">
        <aside className="md:w-1/3">
          <ul className="flex max-h-80 flex-col gap-2 overflow-y-auto pr-2 text-sm">
            {sortedFiles.map((file) => (
              <li key={file}>
                <button
                  type="button"
                  onClick={() => handleSelect(file)}
                  className={`w-full rounded-md border px-3 py-2 text-left transition ${
                    selected === file
                      ? 'border-echo-pulse bg-echo-pulse/10 text-echo-pulse'
                      : 'border-transparent bg-slate-800/60 text-slate-200 hover:border-slate-700'
                  }`}
                >
                  {file}
                </button>
              </li>
            ))}
            {!sortedFiles.length && <li className="text-slate-500">No logs found.</li>}
          </ul>
          {error && <p className="mt-4 text-xs text-rose-400">{error}</p>}
        </aside>
        <section className="flex flex-1 flex-col gap-4 md:w-2/3">
          {selected ? (
            <div className="flex h-full flex-col gap-3">
              <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-white">{selected}</h3>
                  <p className="text-xs text-slate-400">
                    Follow the live stream or navigate historical slices using the controls below.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => void loadOlder()}
                    disabled={loadingOlder || !firstChunk?.hasMoreBackward}
                    className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 font-medium text-slate-200 transition hover:border-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loadingOlder ? 'Loading…' : 'Load older'}
                  </button>
                  <button
                    type="button"
                    onClick={() => void loadNewer()}
                    disabled={loadingNewer || !lastChunk}
                    className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 font-medium text-slate-200 transition hover:border-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loadingNewer ? 'Loading…' : 'Load newer'}
                  </button>
                  <button
                    type="button"
                    onClick={() => void loadLatest()}
                    disabled={loadingLatest}
                    className="rounded-md border border-echo-pulse/60 bg-echo-pulse/10 px-3 py-2 font-medium text-echo-pulse transition hover:bg-echo-pulse/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loadingLatest ? 'Refreshing…' : 'Jump to latest'}
                  </button>
                  <button
                    type="button"
                    aria-pressed={follow}
                    onClick={handleFollowToggle}
                    className={`rounded-md border px-3 py-2 font-medium transition ${
                      follow
                        ? 'border-emerald-500 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20'
                        : 'border-slate-700 bg-slate-900 text-slate-200 hover:border-slate-600'
                    }`}
                  >
                    {follow ? 'Following tail' : 'Follow tail'}
                  </button>
                </div>
              </header>
              <pre
                ref={scrollRef}
                className="max-h-96 flex-1 overflow-y-auto rounded-lg bg-slate-950/80 p-4 text-xs leading-relaxed text-slate-200"
              >
                {combinedLog || '∅ No log entries available. Load older slices or wait for new activity.'}
              </pre>
              {streamError && <p className="text-xs text-rose-400" role="status">{streamError}</p>}
            </div>
          ) : (
            <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-900/60 p-8 text-center text-sm text-slate-400">
              Select a log file to review Echo Computer activity.
            </div>
          )}
        </section>
      </div>
    </article>
  );
}
