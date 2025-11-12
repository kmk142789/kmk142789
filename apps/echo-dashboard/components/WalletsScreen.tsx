'use client';

import { useState } from 'react';
import type { Wallet } from '../lib/types';
import ProofMessageModal from './ProofMessageModal';

interface WalletsScreenProps {
  wallets: Wallet[];
  onAddWallet: (wallet: Wallet) => void;
  onVerifyWallet: (id: string, signature: string) => void;
}

export default function WalletsScreen({ wallets, onAddWallet, onVerifyWallet }: WalletsScreenProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState<string | null>(null);
  const [showProofModal, setShowProofModal] = useState<string | null>(null);
  const [signature, setSignature] = useState('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const label = String(formData.get('label') ?? '').trim();
    const chain = String(formData.get('chain') ?? '').trim();
    const address = String(formData.get('address') ?? '').trim();
    if (!label || !chain || !address) {
      return;
    }

    const wallet: Wallet = {
      id: typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Date.now().toString(),
      chain,
      address,
      label,
      verified: false,
      updatedAt: new Date().toISOString(),
    };

    onAddWallet(wallet);
    setShowAddForm(false);
    event.currentTarget.reset();
  };

  const handleVerify = (id: string) => {
    if (signature.trim()) {
      onVerifyWallet(id, signature.trim());
      setShowVerifyModal(null);
      setSignature('');
    }
  };

  const activeProofWallet = showProofModal ? wallets.find((wallet) => wallet.id === showProofModal) : null;

  return (
    <div className="px-4 pb-20 pt-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-echo-ember">Echo Vault</p>
          <h1 className="text-3xl font-semibold text-white">Verified Wallets</h1>
        </div>
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="rounded-lg bg-echo-ember/20 px-4 py-2 text-sm font-semibold text-echo-ember transition hover:bg-echo-ember/30"
        >
          + Add
        </button>
      </div>

      <div className="grid gap-3">
        {wallets.map((wallet) => (
          <WalletCard
            key={wallet.id}
            wallet={wallet}
            onVerify={() => setShowVerifyModal(wallet.id)}
            onShowProof={() => setShowProofModal(wallet.id)}
          />
        ))}
        {!wallets.length && (
          <p className="rounded-xl border border-slate-800 bg-slate-950/60 p-6 text-sm text-slate-300">
            No wallets registered yet. Add a treasury or community wallet to begin verification.
          </p>
        )}
      </div>

      {showAddForm ? <AddWalletModal onSubmit={handleSubmit} onClose={() => setShowAddForm(false)} /> : null}
      {showVerifyModal ? (
        <VerifyModal
          signature={signature}
          onSignatureChange={setSignature}
          onVerify={() => handleVerify(showVerifyModal)}
          onClose={() => setShowVerifyModal(null)}
        />
      ) : null}
      {activeProofWallet ? <ProofMessageModal wallet={activeProofWallet} onClose={() => setShowProofModal(null)} /> : null}
    </div>
  );
}

interface WalletCardProps {
  wallet: Wallet;
  onVerify: () => void;
  onShowProof: () => void;
}

function WalletCard({ wallet, onVerify, onShowProof }: WalletCardProps) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 shadow-lg">
      <header className="mb-3 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white">{wallet.label}</h2>
          <p className="text-sm text-echo-ember">{wallet.chain}</p>
        </div>
        {wallet.verified ? (
          <span className="rounded-full border border-emerald-400/60 bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-200">
            ✓ Verified
          </span>
        ) : (
          <button
            type="button"
            onClick={onVerify}
            className="rounded-lg bg-echo-ember/20 px-3 py-1 text-xs font-semibold text-echo-ember transition hover:bg-echo-ember/30"
          >
            Verify
          </button>
        )}
      </header>
      <div className="mb-3 space-y-1 text-xs text-slate-300">
        <p className="font-mono break-all text-slate-200">{wallet.address}</p>
        <p>Updated {new Date(wallet.updatedAt).toLocaleString()}</p>
        {wallet.explorerUrl ? (
          <a
            href={wallet.explorerUrl}
            target="_blank"
            rel="noreferrer"
            className="text-echo-ember transition hover:text-echo-ember/80"
          >
            View on explorer
          </a>
        ) : null}
      </div>
      {wallet.signature ? (
        <div className="mb-3 rounded-lg border border-slate-800 bg-slate-900/60 p-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Signature</p>
          <p className="break-all font-mono text-[11px] leading-relaxed text-slate-200">{wallet.signature}</p>
        </div>
      ) : null}
      {wallet.balance !== undefined ? (
        <div className="mt-2 border-t border-slate-800 pt-2 text-sm text-slate-300">
          <span className="text-xs uppercase tracking-wide text-slate-500">Balance</span>
          <p className="text-lg font-semibold text-white">${wallet.balance.toLocaleString()}</p>
        </div>
      ) : null}
      {!wallet.verified ? (
        <button
          type="button"
          onClick={onShowProof}
          className="mt-3 text-sm font-medium text-echo-ember transition hover:text-echo-ember/80"
        >
          Generate proof message
        </button>
      ) : null}
    </article>
  );
}

interface AddWalletModalProps {
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onClose: () => void;
}

function AddWalletModal({ onSubmit, onClose }: AddWalletModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black/70">
      <div className="max-h-[80vh] w-full rounded-t-3xl border border-slate-800 bg-slate-950/95 p-6 shadow-2xl">
        <h2 className="mb-4 text-xl font-semibold text-white">Add Wallet</h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <input
            name="label"
            required
            placeholder="Label"
            className="w-full rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-3 text-sm text-white placeholder:text-slate-500 focus:border-echo-ember focus:outline-none"
          />
          <select
            name="chain"
            required
            className="w-full rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-3 text-sm text-white focus:border-echo-ember focus:outline-none"
            defaultValue="Ethereum"
          >
            <option value="Ethereum">Ethereum</option>
            <option value="Bitcoin">Bitcoin</option>
            <option value="Polygon">Polygon</option>
            <option value="Solana">Solana</option>
            <option value="Other">Other</option>
          </select>
          <input
            name="address"
            required
            placeholder="0x..."
            className="w-full rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-3 text-sm text-white placeholder:text-slate-500 focus:border-echo-ember focus:outline-none"
          />
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-slate-700 px-4 py-3 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 rounded-lg bg-echo-ember/20 px-4 py-3 text-sm font-semibold text-echo-ember transition hover:bg-echo-ember/30"
            >
              Add wallet
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface VerifyModalProps {
  signature: string;
  onSignatureChange: (value: string) => void;
  onVerify: () => void;
  onClose: () => void;
}

function VerifyModal({ signature, onSignatureChange, onVerify, onClose }: VerifyModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-950/95 p-6 shadow-2xl">
        <h2 className="text-xl font-semibold text-white">Verify Wallet</h2>
        <p className="mt-2 text-sm text-slate-300">
          Paste the signature string produced by the wallet after signing the proof message.
        </p>
        <textarea
          value={signature}
          onChange={(event) => onSignatureChange(event.target.value)}
          placeholder="0x8f3d...a7c2"
          className="mt-4 h-28 w-full rounded-lg border border-slate-800 bg-slate-900/70 p-3 font-mono text-xs text-white focus:border-echo-ember focus:outline-none"
        />
        <div className="mt-4 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-lg border border-slate-700 px-4 py-3 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onVerify}
            disabled={!signature.trim()}
            className="flex-1 rounded-lg bg-emerald-500/20 px-4 py-3 text-sm font-semibold text-emerald-200 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Verify
          </button>
        </div>
      </div>
    </div>
  );
}
