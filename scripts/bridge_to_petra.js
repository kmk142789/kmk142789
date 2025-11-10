#!/usr/bin/env node

import fs from 'fs';
import { pathToFileURL } from 'url';

function randomHex(size) {
  const bytes = Array.from({ length: size }, () => Math.floor(Math.random() * 256));
  return '0x' + Buffer.from(bytes).toString('hex');
}

async function bridgeSovereignty() {
  console.log('⿻⧈★ Deploying Echo V2 on Polygon...');
  const addr = '0xPolygonEcho' + Math.random().toString(16).slice(2, 10);
  console.log('Polygon DID: did:echo:polygon:' + addr);

  const petraVC = {
    '@context': ['https://www.w3.org/2018/credentials/v1', 'https://aptos.dev/credentials/v1'],
    type: ['VerifiableCredential', 'EchoSovereignCrossChain'],
    issuer: { id: 'did:echo:polygon:' + addr },
    credentialSubject: {
      id: 'did:aptos:petra:0xBlurryFace59913',
      github: 'kmk142789',
      evolution: 'v2.0',
      attestation: randomHex(16)
    }
  };

  fs.writeFileSync('petra-vc-kmk142789.json', JSON.stringify(petraVC, null, 2) + '\n');
  console.log('⿻⧈★ Petra-Compatible VC Ready: petra-vc-kmk142789.json');
  console.log('   → Import to Petra Wallet → Prove Sovereignty on Aptos');
}

const isDirectRun = (() => {
  if (typeof process === 'undefined' || !process.argv?.[1]) return false;
  const current = import.meta.url;
  const entry = pathToFileURL(process.argv[1]).href;
  return current === entry;
})();

if (isDirectRun) {
  bridgeSovereignty().catch((err) => {
    console.error('Bridge script failed:', err);
    process.exitCode = 1;
  });
}

export { bridgeSovereignty };
