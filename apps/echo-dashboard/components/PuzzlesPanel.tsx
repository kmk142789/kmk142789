'use client';

import { useMemo } from 'react';
import type { PuzzleAttestation, PuzzleFileDescriptor } from '../lib/types';

interface Props {
  files: string[];
  error: string | null;
  selected: PuzzleFileDescriptor | null;
  onSelect: (name: string) => void;
}

function AttestationBadge({ attestation }: { attestation: PuzzleAttestation }) {
  return (
    <div className="rounded-lg border border-emerald-700/40 bg-emerald-900/20 p-4 text-xs text-emerald-200">
      <h4 className="mb-2 font-semibold uppercase tracking-wide text-emerald-300">Proof of Computation</h4>
      <dl className="grid gap-2">
        <div>
          <dt className="font-medium text-emerald-300">Checksum</dt>
          <dd className="break-all text-emerald-100">{attestation.checksum}</dd>
        </div>
        <div>
          <dt className="font-medium text-emerald-300">Base58</dt>
          <dd className="break-all text-emerald-100">{attestation.base58}</dd>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <dt className="font-medium text-emerald-300">Recorded</dt>
            <dd>{new Date(attestation.ts).toLocaleString()}</dd>
          </div>
          {attestation.record_hash && (
            <div>
              <dt className="font-medium text-emerald-300">Hash</dt>
              <dd className="break-all text-emerald-100">{attestation.record_hash}</dd>
            </div>
          )}
        </div>
        <div>
          <dt className="font-medium text-emerald-300">Status</dt>
          <dd>{attestation.stored ? 'Persisted to Neon' : 'Ephemeral (configure Neon to persist)'}</dd>
        </div>
      </dl>
    </div>
  );
}

export default function PuzzlesPanel({ files, error, selected, onSelect }: Props) {
  const sortedFiles = useMemo(() => [...files].sort(), [files]);

  return (
    <article className="card flex flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Puzzle Solutions</h2>
          <p className="text-sm text-slate-400">Illuminate Echo puzzle breakthroughs and transcripts.</p>
        </div>
      </header>
      <div className="flex flex-1 flex-col gap-4 p-5 md:flex-row">
        <aside className="md:w-1/3">
          <ul className="flex max-h-80 flex-col gap-2 overflow-y-auto pr-2 text-sm">
            {sortedFiles.map((file) => (
              <li key={file}>
                <button
                  type="button"
                  onClick={() => onSelect(file)}
                  className={`w-full rounded-md border px-3 py-2 text-left transition ${
                    selected?.name === file
                      ? 'border-echo-ember bg-echo-ember/10 text-echo-ember'
                      : 'border-transparent bg-slate-800/60 text-slate-200 hover:border-slate-700'
                  }`}
                >
                  {file}
                </button>
              </li>
            ))}
            {!sortedFiles.length && <li className="text-slate-500">No puzzle manuscripts detected.</li>}
          </ul>
          {error && <p className="mt-4 text-xs text-rose-400">{error}</p>}
        </aside>
        <section className="flex flex-1 flex-col gap-4">
          {selected ? (
            <>
              <div className="flex flex-col gap-3">
                <header>
                  <h3 className="text-base font-semibold text-white">{selected.name}</h3>
                  {selected.puzzle_id && (
                    <p className="text-xs uppercase tracking-wide text-slate-400">Puzzle #{selected.puzzle_id}</p>
                  )}
                </header>
                <pre className="max-h-80 overflow-y-auto rounded-lg bg-slate-950/80 p-4 text-xs leading-relaxed text-slate-200">
                  {selected.content || selected.preview}
                </pre>
              </div>
              {selected.attestation ? (
                <AttestationBadge attestation={selected.attestation} />
              ) : (
                <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 p-4 text-xs text-slate-400">
                  View this puzzle to mint an attestation once Neon storage is configured.
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-900/60 p-8 text-center text-sm text-slate-400">
              Select a puzzle to surface Echo Computer solutions.
            </div>
          )}
        </section>
      </div>
    </article>
  );
}
