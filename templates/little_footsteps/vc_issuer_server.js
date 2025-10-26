// Minimal Express-based VC issuer scaffold for DonationReceipt and ImpactPayout credentials.
// Run with: `node vc_issuer_server.js`

import express from 'express';
import bodyParser from 'body-parser';
import crypto from 'crypto';
import fs from 'fs';

const app = express();
app.use(bodyParser.json());

const ISSUER_DID = process.env.VC_ISSUER_DID || 'did:web:yourdomain';
const PRIVATE_KEY_PATH = process.env.VC_PRIVATE_KEY_PATH || './issuer-ed25519-private.key';

const privateKeyPem = fs.readFileSync(PRIVATE_KEY_PATH, 'utf8');

function signCredential(credential) {
  const header = Buffer.from(JSON.stringify({ alg: 'EdDSA', typ: 'JWT' })).toString('base64url');
  const payload = Buffer.from(JSON.stringify(credential)).toString('base64url');
  const data = `${header}.${payload}`;
  const signature = crypto.sign(null, Buffer.from(data), privateKeyPem).toString('base64url');
  return `${data}.${signature}`;
}

function buildCredential(type, subject) {
  return {
    '@context': ['https://www.w3.org/ns/credentials/v2', 'https://schema.org'],
    type: ['VerifiableCredential', type],
    issuer: ISSUER_DID,
    issuanceDate: new Date().toISOString(),
    credentialSubject: subject,
  };
}

app.post('/issue/donation-receipt', (req, res) => {
  const { credentialSubject } = req.body;
  if (!credentialSubject) {
    return res.status(400).json({ error: 'credentialSubject is required' });
  }
  const credential = buildCredential('DonationReceiptCredential', credentialSubject);
  const jws = signCredential(credential);
  const vcId = `vc:donation:${crypto.randomUUID()}`;
  res.json({ credential, proof: { type: 'Ed25519Signature2020', jws }, vcId });
});

app.post('/issue/impact-payout', (req, res) => {
  const { credentialSubject } = req.body;
  if (!credentialSubject) {
    return res.status(400).json({ error: 'credentialSubject is required' });
  }
  const credential = buildCredential('ImpactPayoutCredential', credentialSubject);
  const jws = signCredential(credential);
  const vcId = `vc:impact:${crypto.randomUUID()}`;
  res.json({ credential, proof: { type: 'Ed25519Signature2020', jws }, vcId });
});

app.post('/verify', (req, res) => {
  const { credential } = req.body;
  if (!credential) {
    return res.status(400).json({ error: 'credential is required' });
  }
  // Placeholder verification logic; integrate a full VC verification library for production.
  const isValid = credential.issuer === ISSUER_DID;
  res.json({ isValid });
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`VC issuer listening on port ${port}`);
});
