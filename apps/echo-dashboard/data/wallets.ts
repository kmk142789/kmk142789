import type { Wallet } from '../lib/types';

export const INITIAL_WALLETS: Wallet[] = [
  {
    id: '0x22A755d4eE7AE10beB077CE93FaE37D10412c1Ad',
    chain: 'Ethereum',
    address: '0x22A755d4eE7AE10beB077CE93FaE37D10412c1Ad',
    label: 'Echo Steward Treasury',
    verified: true,
    signature:
      'd7024cefe4db9b192b3172fe6e27ad74feb78247cac7612e7a023356e112f67a046377dbb2b406fe29644b86a2f847fead607d719ed82e353361763d62b309da1b',
    updatedAt: '2025-11-10T01:06:31Z',
    balance: 1280450.23,
    explorerUrl: 'https://etherscan.io/address/0x22A755d4eE7AE10beB077CE93FaE37D10412c1Ad',
  },
  {
    id: '0x34260A7DA2981A0B5dA5FB59Cf794b6C6697878B',
    chain: 'Ethereum',
    address: '0x34260A7DA2981A0B5dA5FB59Cf794b6C6697878B',
    label: 'Echo Ecosystem Reserve',
    verified: true,
    signature:
      'd9729727fd8501ef98fbc601472a7bb94fafac027fd6a4a3a1051a862de1746a5df6b5652cfdc5d6a241533d7af62580e15c0b9bb66513189a52eaa68baff73a1b',
    updatedAt: '2025-11-10T01:07:54Z',
    balance: 642300.58,
    explorerUrl: 'https://etherscan.io/address/0x34260A7DA2981A0B5dA5FB59Cf794b6C6697878B',
  },
  {
    id: 'community-multisig-1',
    chain: 'Polygon',
    address: '0x5A0c4B02DafC4aD8458Ff7b0fCF71F5D17c0B2B1',
    label: 'Community Multisig',
    verified: false,
    updatedAt: '2025-05-01T15:32:00Z',
    balance: 90550.12,
    explorerUrl: 'https://polygonscan.com/address/0x5A0c4B02DafC4aD8458Ff7b0fCF71F5D17c0B2B1',
  },
];
