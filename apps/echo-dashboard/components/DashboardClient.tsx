'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';
import { API_BASE, apiDelete, apiGet, apiPost } from '../lib/api';
import type {
  CliCommand,
  CliResult,
  NeonKeyRecord,
  PuzzleFileDescriptor,
  CodexRegistryResponse,
} from '../lib/types';
import LogsPanel from './LogsPanel';
import PuzzlesPanel from './PuzzlesPanel';
import CliRunner from './CliRunner';
import NeonKeyManager from './NeonKeyManager';
import CodexSummaryCard from './CodexSummaryCard';
import MetricsPanel from './MetricsPanel';

interface LogsResponse {
  files: string[];
}

interface PuzzlesResponse {
  files: string[];
}

interface CliCommandsResponse {
  commands: CliCommand[];
}

interface NeonKeyResponse {
  keys: NeonKeyRecord[];
}

const fetcher = async (path: string) => apiGet(path);

export default function DashboardClient() {
  const [selectedLog, setSelectedLog] = useState<string | null>(null);
  const [puzzleContent, setPuzzleContent] = useState<PuzzleFileDescriptor | null>(null);
  const [cliResult, setCliResult] = useState<CliResult | null>(null);
  const [cliLoading, setCliLoading] = useState(false);
  const [neonError, setNeonError] = useState<string | null>(null);

  const { data: logFiles, error: logError } = useSWR<LogsResponse>('/logs', fetcher);
  const { data: puzzleFiles, error: puzzleError } = useSWR<PuzzlesResponse>('/puzzles', fetcher);
  const { data: cliCommands } = useSWR<CliCommandsResponse>('/cli/commands', fetcher);
  const { data: codexRegistry } = useSWR<CodexRegistryResponse>('/api/codex', fetcher);
  const { data: neonKeys, error: neonFetchError, mutate: refreshNeonKeys } = useSWR<NeonKeyResponse>(
    '/neon/keys',
    async (path) => {
      try {
        return await apiGet(path);
      } catch (error) {
        if (error instanceof Error && error.message.includes('503')) {
          setNeonError('Neon database not configured. Add `NEON_DATABASE_URL` to enable key storage.');
        } else {
          setNeonError('Failed to load Neon keys.');
        }
        throw error;
      }
    }
  );

  useEffect(() => {
    if (neonFetchError) {
      console.warn('Neon key fetch failed', neonFetchError);
    }
  }, [neonFetchError]);

  useEffect(() => {
    if (neonKeys) {
      setNeonError(null);
    }
  }, [neonKeys]);

  useEffect(() => {
    if (!selectedLog || !logFiles?.files) return;
    if (!logFiles.files.includes(selectedLog)) {
      setSelectedLog(null);
    }
  }, [logFiles, selectedLog]);

  const handleSelectPuzzle = useCallback(async (name: string) => {
    try {
      const response = await apiGet<PuzzleFileDescriptor>(`/puzzles/${encodeURIComponent(name)}`);
      setPuzzleContent(response);
    } catch (error) {
      console.error('Unable to read puzzle', error);
    }
  }, []);

  const handleRunCli = useCallback(
    async (command: string, args: string[]) => {
      setCliLoading(true);
      setCliResult(null);
      try {
        const result = await apiPost<CliResult>('/cli/run', { command, args });
        setCliResult(result);
      } catch (error) {
        if (error instanceof Error) {
          setCliResult({ code: null, stdout: '', stderr: error.message });
        }
      } finally {
        setCliLoading(false);
      }
    },
    []
  );

  const handleCreateNeonKey = useCallback(
    async (label: string, value: string) => {
      await apiPost('/neon/keys', { label, value });
      await refreshNeonKeys();
    },
    [refreshNeonKeys]
  );

  const handleDeleteNeonKey = useCallback(
    async (id: string) => {
      await apiDelete(`/neon/keys/${id}`);
      await refreshNeonKeys();
    },
    [refreshNeonKeys]
  );

  const cliCommandOptions = useMemo(() => cliCommands?.commands ?? [], [cliCommands]);

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="badge text-echo-ember">EchoEvolver ∇⊸≋∇</p>
          <h1 className="text-3xl font-semibold text-white md:text-4xl">Echo Control Nexus</h1>
          <p className="text-slate-300">
            Bridge EchoOS telemetry, Echo Computer sandboxes, and Neon banking rituals in one orbit.
          </p>
        </div>
        <div className="text-xs text-slate-400">
          <p>API: {API_BASE}</p>
        </div>
      </header>

      <section>
        <MetricsPanel />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <LogsPanel
          files={logFiles?.files ?? []}
          error={logError ? 'Unable to load Echo Computer logs.' : null}
          selected={selectedLog}
          onSelect={setSelectedLog}
        />
        <PuzzlesPanel
          files={puzzleFiles?.files ?? []}
          error={puzzleError ? 'Unable to load puzzle solutions.' : null}
          selected={puzzleContent}
          onSelect={handleSelectPuzzle}
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <CliRunner
          commands={cliCommandOptions}
          onRun={handleRunCli}
          loading={cliLoading}
          result={cliResult}
        />
        <NeonKeyManager
          records={neonKeys?.keys ?? []}
          error={neonError}
          onCreate={handleCreateNeonKey}
          onDelete={handleDeleteNeonKey}
        />
      </section>

      <section>
        <CodexSummaryCard items={codexRegistry?.items ?? []} generatedAt={codexRegistry?.generated_at} />
      </section>
    </main>
  );
}
