// Simple evolution + status module for Echo Dominion node

import fs from 'fs';
import path from 'path';
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

function getStatus() {
  const state = loadJson(STATE_PATH);
  const gov = loadJson(GOV_PATH);

  return {
    sovereignty: 'soft-local',
    version: state.version,
    families_helped: state.families_helped,
    guardians_count: state.guardians.length,
    treasury_usd: state.treasury_usd,
    core_mission: gov.core_mission,
    constraints: gov.constraints,
    last_evolution_run_iso: state.last_evolution_run_iso
  };
}

function runEvolution() {
  const state = loadJson(STATE_PATH);
  const gov = loadJson(GOV_PATH);

  const now = new Date().toISOString();

  const narrative = [
    `Current families helped: ${state.families_helped}.`,
    `Guardians: ${state.guardians.length}.`,
    `Treasury (USD, off-chain placeholder): ${state.treasury_usd}.`,
    '',
    'Recommended next steps:',
    '- Add a real relief request log (who, when, amount) to echo_state.json.',
    '- Implement a simple verifiable credential stub for guardians and recipients.',
    '- Expose /echo/status and /echo/evolve HTTP endpoints on the node.',
    '- Start tracking a weekly metric snapshot for families_helped and treasury_usd.'
  ].join('\n');

  state.last_evolution_run_iso = now;
  saveJson(STATE_PATH, state);
  appendJournal(narrative);

  return {
    ok: true,
    ran_at: now,
    message: 'Evolution cycle recorded.',
    recommendations: [
      'Implement relief request log structure.',
      'Add VC issuer stub for guardian/recipient roles.',
      'Wire /echo/status and /echo/evolve into HTTP server.',
      'Start weekly metric snapshots.'
    ]
  };
}

export { getStatus, runEvolution };
