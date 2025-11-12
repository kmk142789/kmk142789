'use client';

import { useCallback, useState } from 'react';
import WalletsScreen from '../../components/WalletsScreen';
import type { Wallet } from '../../lib/types';
import { INITIAL_WALLETS } from '../../data/wallets';

export default function WalletsPage() {
  const [wallets, setWallets] = useState<Wallet[]>(INITIAL_WALLETS);

  const handleAddWallet = useCallback((wallet: Wallet) => {
    setWallets((previous) => [wallet, ...previous]);
  }, []);

  const handleVerifyWallet = useCallback((id: string, signature: string) => {
    setWallets((previous) =>
      previous.map((wallet) =>
        wallet.id === id
          ? {
              ...wallet,
              verified: true,
              signature,
              updatedAt: new Date().toISOString(),
            }
          : wallet,
      ),
    );
  }, []);

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10">
      <WalletsScreen wallets={wallets} onAddWallet={handleAddWallet} onVerifyWallet={handleVerifyWallet} />
    </main>
  );
}
