import { loadState } from './relief_ledger.js';

function resolveDid(didUrl) {
  if (!didUrl || !didUrl.startsWith('did:echo:')) {
    return null;
  }

  const state = loadState();
  const guardian = state.guardians?.find((g) => g.did_url === didUrl);

  if (!guardian || !guardian.public_key_ed25519_multibase) {
    return null;
  }

  const keyReference = `${didUrl}#key-1`;

  return {
    '@context': 'https://w3id.org/did/v1',
    id: didUrl,
    verificationMethod: [
      {
        id: keyReference,
        type: 'Ed25519VerificationKey2018',
        controller: didUrl,
        publicKeyMultibase: guardian.public_key_ed25519_multibase
      }
    ],
    authentication: [keyReference],
    assertionMethod: [keyReference]
  };
}

export { resolveDid };
