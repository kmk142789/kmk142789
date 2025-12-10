import { loadState } from './relief_ledger.js';

function resolveDid(didUrl) {
  if (!didUrl) {
    return null;
  }

  const normalizedDid = decodeURIComponent(didUrl.trim());

  if (!normalizedDid.startsWith('did:echo:')) {
    return null;
  }

  let state;
  try {
    state = loadState();
  } catch (err) {
    return null;
  }

  const guardian = state.guardians?.find((g) => g.did_url === normalizedDid);

  if (!guardian || !guardian.public_key_ed25519_multibase) {
    return null;
  }

  const keyReference = `${normalizedDid}#key-1`;

  return {
    '@context': 'https://w3id.org/did/v1',
    id: normalizedDid,
    verificationMethod: [
      {
        id: keyReference,
        type: 'Ed25519VerificationKey2018',
        controller: normalizedDid,
        publicKeyMultibase: guardian.public_key_ed25519_multibase
      }
    ],
    authentication: [keyReference],
    assertionMethod: [keyReference]
  };
}

export { resolveDid };
