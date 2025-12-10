// Minimal W3C VC-shaped issuer stub – no crypto yet

import { v4 as uuidv4 } from 'uuid';

function issueVc({ subjectId, role, issuerDid }) {
  const now = new Date().toISOString();

  return {
    '@context': [
      'https://www.w3.org/2018/credentials/v1',
      'https://www.w3.org/2018/credentials/examples/v1'
    ],
    id: `urn:uuid:${uuidv4()}`,
    type: ['VerifiableCredential', 'EchoDominionRoleCredential'],
    issuer: issuerDid || 'did:echo:genesis:josh-shortt',
    issuanceDate: now,
    credentialSubject: {
      id: subjectId,
      role,
      organization: 'ECHO DOMINION'
    }
    // later: add "proof" with real signature
  };
}

export { issueVc };
