function issueVerifiableCredential(signedEvent) {
  if (!signedEvent || !signedEvent.attestation_block) {
    throw new Error('Signed event is missing attestation data');
  }

  const { attestation_block: attestationBlock, id, at_iso: atIso, signature } = signedEvent;

  if (!attestationBlock.issuer_did) {
    throw new Error('Issuer DID is required to build a verifiable credential');
  }

  const keyReference = `${attestationBlock.issuer_did}#key-1`;

  const vcPayload = {
    '@context': [
      'https://www.w3.org/2018/credentials/v1',
      'https://schema.org/'
    ],
    id: `did:echo:vc:${id}`,
    type: ['VerifiableCredential', 'ReliefAttestation'],
    issuer: attestationBlock.issuer_did,
    issuanceDate: atIso,
    credentialSubject: {
      id: 'did:echo:subject:redacted',
      type: 'ReliefBeneficiary',
      financial_commitment: attestationBlock.satoshi_commitment_hash,
      reason_category: attestationBlock.puzzle_attestations?.reason_category
    },
    proof: {
      type: 'Ed25519Signature2018',
      verificationMethod: keyReference,
      created: atIso,
      proofPurpose: 'assertionMethod',
      jws: signature
    }
  };

  return vcPayload;
}

export { issueVerifiableCredential };
