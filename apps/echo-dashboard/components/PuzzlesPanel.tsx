'use client';

import { useMemo } from 'react';
import type { FileDescriptor } from '../lib/types';

interface Props {
  files: string[];
  error: string | null;
  selected: FileDescriptor | null;
  onSelect: (name: string) => void;
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
        <section className="md:w-2/3">
          {selected ? (
            <div className="flex h-full flex-col gap-3">
              <header>
                <h3 className="text-base font-semibold text-white">{selected.name}</h3>
              </header>
              <pre className="max-h-80 overflow-y-auto rounded-lg bg-slate-950/80 p-4 text-xs leading-relaxed text-slate-200">
                {selected.content || selected.preview}
              </pre>
            </div>
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
