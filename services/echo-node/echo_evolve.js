// Evolution + status module for Echo Dominion node (v0.6.0)

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const STATE_PATH = path.join(__dirname, 'state', 'echo_state.json');
const GOV_PATH = path.join(__dirname, '..', '..', 'governance', 'echo_governance.json');
const JOURNAL_PATH = path.join(__dirname, 'state', 'evolution_journal.md');

function loadJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function saveJson(p, value) {
  fs.writeFileSync(p, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

function appendJournal(entry) {
  const line = `\n## ${new Date().toISOString()}\n\n${entry}\n`;
  fs.appendFileSync(JOURNAL_PATH, line, 'utf8');
}

function stableObject(value) {
  if (Array.isArray(value)) {
    return value.map(stableObject);
  }
  if (value && typeof value === 'object') {
    return Object.keys(value)
      .sort()
      .reduce((acc, key) => {
        acc[key] = stableObject(value[key]);
        return acc;
      }, {});
  }
  return value;
}

function computeStateHash(state) {
  return crypto
    .createHash('sha256')
    .update(JSON.stringify(stableObject(state)))
    .digest('hex');
}

function getStatus() {
  const state = loadJson(STATE_PATH);
  const gov = loadJson(GOV_PATH);

  return {
    sovereignty: 'soft-local',
    version: state.version,
    node_name: state.node_name,
    operational_status: state.operational_status,
    families_helped: state.families_helped,
    guardians_count: state.guardians.length,
    treasury_usd: state.treasury_usd,
    attestation_service_did: state.attestation_service_did,
    core_mission: gov.core_mission,
    constraints: gov.constraints,
    last_evolution_run_iso: state.last_evolution_run_iso
  };
}

function runEvolution() {
  const state = loadJson(STATE_PATH);

  const nowIso = new Date().toISOString();
  const snapshot = {
    families_helped: state.families_helped || 0,
    total_relief_usd: (state.relief_ledger || []).reduce(
      (acc, evt) => acc + Number(evt.amount_usd || 0),
      0
    ),
    event_count: (state.relief_ledger || []).length,
    treasury_usd: state.treasury_usd || 0
  };

  state.last_evolution_run_iso = nowIso;
  state.schema_hash = computeStateHash(state);
  saveJson(STATE_PATH, state);

  const narrative = `
ECHO DOMINION EVOLUTION REPORT (v0.6.0) — ${nowIso}
——————————————————————————————————————————————
Families Helped: ${snapshot.families_helped}
Total Sovereign Relief Distributed: $${snapshot.total_relief_usd.toFixed(2)}
Events Recorded: ${snapshot.event_count}
Treasury Remaining (On-Node Estimate): $${snapshot.treasury_usd.toFixed(2)}
State Hash Integrity: ${state.schema_hash}

SOVEREIGN DIRECTIVES (Next Iteration Mandates):
→ **DID Resolution Core:** Implement the did:echo: method resolver.
→ **VC Issuance:** Create a dedicated /vc/issue endpoint that wraps a fully signed ledger event into a W3C-compliant Verifiable Credential.
→ **Treasury Commitment Verification:** Implement an endpoint that verifies the satoshi_commitment_hash against the external on-chain transaction data (requires external oracle/bridge).
→ **ZKP Readiness:** Develop the initial zero-knowledge proof circuit to selectively disclose the reason_category without revealing the beneficiary_hint_hash.

The commitment hash is law. The puzzle is self-solving.
`;

  appendJournal(narrative);

  return {
    ok: true,
    snapshot,
    directives: ['did_resolver', 'vc_issuance', 'commitment_verification', 'zkp_readiness']
  };
}

export { getStatus, runEvolution };
