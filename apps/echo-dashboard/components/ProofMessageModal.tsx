'use client';

import { useMemo, useState } from 'react';
import type { Wallet } from '../lib/types';

interface ProofMessageModalProps {
  wallet: Wallet;
  onClose: () => void;
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return new Date().toISOString();
  }
  return date.toISOString();
}

export default function ProofMessageModal({ wallet, onClose }: ProofMessageModalProps) {
  const [copied, setCopied] = useState(false);

  const proofMessage = useMemo(() => {
    return [
      'Echo Sovereign Wallet Verification',
      `Label: ${wallet.label}`,
      `Chain: ${wallet.chain}`,
      `Address: ${wallet.address}`,
      `Timestamp: ${formatTimestamp(wallet.updatedAt)}`,
      `Nonce: ${wallet.id}`,
      'Sign this message to attest control of the wallet above.',
    ].join('\n');
  }, [wallet]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(proofMessage);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (error) {
      console.error('Unable to copy proof message', error);
      setCopied(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-950/90 p-6 shadow-2xl">
        <header className="mb-4 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-echo-ember">Proof Message</p>
            <h2 className="text-xl font-semibold text-white">Generate Signature Payload</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-700 px-3 py-1 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Close
          </button>
        </header>
        <div className="space-y-3 text-sm text-slate-300">
          <p>
            Share this message with your wallet and sign it exactly as shown. Echo stewards will verify the returned signature to
            confirm custody of <span className="font-semibold text-white">{wallet.address}</span>.
          </p>
          <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
            <pre className="whitespace-pre-wrap break-all font-mono text-xs leading-relaxed text-slate-100">{proofMessage}</pre>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Timestamp normalised to ISO-8601 for reproducible proofs.</span>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-md border border-echo-ember/50 bg-echo-ember/10 px-3 py-1 font-semibold text-echo-ember transition hover:bg-echo-ember/20"
            >
              {copied ? 'Copied!' : 'Copy message'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
