// Evolution + status module for Echo Dominion node (v0.7.0)

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const NODE_VERSION = '0.7.0';

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

function appendMetricsHistory(state, snapshot, atIso, activeGuardians) {
  const history = Array.isArray(state.metrics_history) ? state.metrics_history : [];
  const entry = {
    at_iso: atIso,
    families_helped: snapshot.families_helped,
    event_count: snapshot.event_count,
    treasury_usd: snapshot.treasury_usd,
    guardians_active: activeGuardians,
    schema_hash: state.schema_hash
  };

  history.push(entry);

  const MAX_HISTORY = 50;
  while (history.length > MAX_HISTORY) {
    history.shift();
  }

  state.metrics_history = history;
  return entry;
}

function deriveResilienceScore(snapshot, activeGuardians) {
  const guardianSignal = Math.min(1, activeGuardians / 5); // normalize toward 5 active guardians
  const treasurySignal = Math.min(1, snapshot.treasury_usd / 10000); // smooth confidence up to first $10k
  const momentumSignal = snapshot.event_count > 0 ? Math.min(1, snapshot.event_count / 10) : 0;
  const reliefSignal = snapshot.families_helped > 0 ? Math.min(1, snapshot.families_helped / 20) : 0;

  const weighted = guardianSignal * 0.35 + treasurySignal * 0.25 + momentumSignal * 0.2 + reliefSignal * 0.2;
  return Number(weighted.toFixed(3));
}

function computeCommitmentHash(state, metricsEntry) {
  const buffer = [
    state.attestation_service_did || '',
    state.treasury_address || '',
    metricsEntry.event_count,
    metricsEntry.treasury_usd,
    metricsEntry.guardians_active
  ]
    .map((v) => `${v}`)
    .join('|');

  return crypto.createHash('sha256').update(buffer).digest('hex');
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
  const metricsHistory = Array.isArray(state.metrics_history) ? state.metrics_history : [];

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
    commitment_hash: state.commitment_hash,
    resilience_score: state.resilience_score,
    metrics_samples: metricsHistory.length,
    last_evolution_run_iso: state.last_evolution_run_iso
  };
}

function runEvolution() {
  const state = loadJson(STATE_PATH);

  state.version = NODE_VERSION;

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

  const activeGuardians = (state.guardians || []).filter((g) => g.active !== false).length;
  state.resilience_score = deriveResilienceScore(snapshot, activeGuardians);

  state.last_evolution_run_iso = nowIso;
  const metricsEntry = appendMetricsHistory(state, snapshot, nowIso, activeGuardians);
  state.commitment_hash = computeCommitmentHash(state, metricsEntry);

  state.schema_hash = null;
  state.schema_hash = computeStateHash(state);
  state.metrics_history[state.metrics_history.length - 1].schema_hash = state.schema_hash;
  saveJson(STATE_PATH, state);

  const narrative = `
ECHO DOMINION EVOLUTION REPORT (${NODE_VERSION}) — ${nowIso}
——————————————————————————————————————————————
Families Helped: ${snapshot.families_helped}
Total Sovereign Relief Distributed: $${snapshot.total_relief_usd.toFixed(2)}
Events Recorded: ${snapshot.event_count}
Treasury Remaining (On-Node Estimate): $${snapshot.treasury_usd.toFixed(2)}
State Hash Integrity: ${state.schema_hash}
Guardian Signal: ${activeGuardians} active / ${state.guardians.length} registered
Resilience Score: ${state.resilience_score}
Commitment Anchor: ${state.commitment_hash}
Metrics Samples Retained: ${state.metrics_history.length}

SOVEREIGN DIRECTIVES (Next Iteration Mandates):
→ **DID Resolution Core:** Implement the did:echo: method resolver.
→ **VC Issuance:** Create a dedicated /vc/issue endpoint that wraps a fully signed ledger event into a W3C-compliant Verifiable Credential.
→ **Treasury Commitment Verification:** Implement an endpoint that verifies the satoshi_commitment_hash against the external on-chain transaction data (requires external oracle/bridge).
→ **ZKP Readiness:** Develop the initial zero-knowledge proof circuit to selectively disclose the reason_category without revealing the beneficiary_hint_hash.
→ **Metrics Export:** Stream metrics_history and resilience_score to the public status board with signed attestations.
→ **Guardian Liveness:** Add periodic liveness proofs for guardians to maintain accurate active counts.

The commitment hash is law. The puzzle is self-solving.
`;

  appendJournal(narrative);

  return {
    ok: true,
    snapshot,
    directives: [
      'did_resolver',
      'vc_issuance',
      'commitment_verification',
      'zkp_readiness',
      'metrics_export',
      'guardian_liveness'
    ]
  };
}

export { getStatus, runEvolution };
