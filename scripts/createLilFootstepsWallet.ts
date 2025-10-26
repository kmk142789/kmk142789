import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Wallet } from 'ethers';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function main() {
  const wallet = Wallet.createRandom();
  const output = {
    address: wallet.address,
    mnemonic: wallet.mnemonic?.phrase ?? null,
    privateKey: wallet.privateKey,
    createdAt: new Date().toISOString(),
    purpose: 'Lil Footsteps daycare treasury',
  } as const;

  const ledgerDir = resolve(__dirname, '..', 'ledger');
  mkdirSync(ledgerDir, { recursive: true });
  const dest = resolve(ledgerDir, 'lil_footsteps_wallet.json');
  writeFileSync(dest, JSON.stringify(output, null, 2));
  console.log(`Lil Footsteps wallet generated and written to ${dest}`);
  console.log(`Address: ${output.address}`);
  if (output.mnemonic) {
    console.log(`Mnemonic: ${output.mnemonic}`);
  }
}

main();
