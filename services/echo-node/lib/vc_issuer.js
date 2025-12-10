function issueVerifiableCredential(signedEvent) {
  const vcPayload = {
    '@context': [
      'https://www.w3.org/2018/credentials/v1',
      'https://schema.org/'
    ],
    id: `did:echo:vc:${signedEvent.id}`,
    type: ['VerifiableCredential', 'ReliefAttestation'],
    issuer: signedEvent.attestation_block.issuer_did,
    issuanceDate: signedEvent.at_iso,
    credentialSubject: {
      id: 'did:echo:subject:redacted',
      type: 'ReliefBeneficiary',
      financial_commitment: signedEvent.attestation_block.satoshi_commitment_hash,
      reason_category: signedEvent.attestation_block.puzzle_attestations.reason_category
    },
    proof: {
      type: 'Ed25519Signature2018',
      verificationMethod: `${signedEvent.attestation_block.issuer_did}#key-1`,
      created: signedEvent.at_iso,
      proofPurpose: 'assertionMethod',
      jws: signedEvent.signature
    }
  };

  return vcPayload;
}

export { issueVerifiableCredential };
