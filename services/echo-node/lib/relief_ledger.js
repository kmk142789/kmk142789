import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { signEvent, verifyEvent, PUBLIC_KEY_MULTIBASE } from './crypto_core.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const STATE_PATH = path.join(__dirname, '..', 'state', 'echo_state.json');

let TREASURY_ADDRESS = 'bc1q...';

function loadState() {
  return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
}

function saveState(state) {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + '\n', 'utf8');
}

function generateEventId(seed) {
  const source = seed || new Date().toISOString();
  return `relief-${crypto.createHash('sha256').update(source).digest('hex').slice(0, 12)}`;
}

function validateReliefEvent(event) {
  if (event.amount_usd == null) {
    throw new Error('Relief event missing amount_usd');
  }
  if (Number.isNaN(Number(event.amount_usd))) {
    throw new Error('Relief event amount_usd must be numeric');
  }
}

function generateSatoshiProof(event, treasury_address) {
  const commitment_data = JSON.stringify({
    amount: event.amount_usd,
    at: event.at_iso,
    to: treasury_address,
    event_id: event.id
  });
  return `sat-sha256:${crypto.createHash('sha256').update(commitment_data).digest('hex')}`;
}

function recordRelief(event) {
  const state = loadState();
  TREASURY_ADDRESS = state.treasury_address || TREASURY_ADDRESS;

  const normalizedAmount = Number(event.amount_usd);
  const normalizedAtIso = event.at_iso || new Date().toISOString();
  validateReliefEvent({ ...event, amount_usd: normalizedAmount });

  const audit_challenge_nonce = crypto.randomBytes(8).toString('hex');

  const normalizedEvent = {
    id: event.id || generateEventId(normalizedAtIso),
    amount_usd: normalizedAmount,
    reason: event.reason || 'unspecified_emergency',
    at_iso: normalizedAtIso,
    approved_by: event.approved_by || 'guardian-1',
    version: '1.3'
  };

  const fullEvent = {
    ...normalizedEvent,
    attestation_block: {
      satoshi_commitment_hash: generateSatoshiProof(normalizedEvent, TREASURY_ADDRESS),
      signed_by_key_multibase: PUBLIC_KEY_MULTIBASE,
      signing_algorithm: 'Ed25519',
      issuer_did: state.attestation_service_did,
      puzzle_attestations: {
        beneficiary_hint_hash: crypto
          .createHash('sha256')
          .update(event.beneficiary_hint || 'redacted')
          .digest('hex'),
        attestation_source: event.attestation_source || 'GuardianDirect',
        reason_category: event.reason_category || 'SovereignRelief.Housing',
        audit_challenge_nonce,
        zero_knowledge_hint: event.zero_knowledge_hint || 'zk-proof-claim-pending'
      }
    },
    signature: null
  };

  const signature = signEvent(fullEvent);
  fullEvent.signature = signature;

  if (!verifyEvent(fullEvent) && signature !== null) {
    throw new Error('CRITICAL: Failed self-verification check post-signing.');
  }

  state.relief_ledger = state.relief_ledger || [];
  state.relief_ledger.push(fullEvent);
  state.families_helped = (state.families_helped || 0) + 1;
  state.treasury_usd = Math.max(0, (state.treasury_usd || 0) - fullEvent.amount_usd);

  saveState(state);
  return { state, event: fullEvent };
}

function verifyLedgerEvent(event) {
  const state = loadState();
  const expectedCommitment = generateSatoshiProof(event, state.treasury_address || TREASURY_ADDRESS);
  const commitmentMatches =
    event.attestation_block?.satoshi_commitment_hash === expectedCommitment;
  return Boolean(commitmentMatches && verifyEvent(event));
}

export { recordRelief, verifyLedgerEvent, generateSatoshiProof, generateEventId };
