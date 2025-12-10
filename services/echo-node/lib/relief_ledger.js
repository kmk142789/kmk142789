import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const STATE_PATH = path.join(__dirname, '..', 'state', 'echo_state.json');

function loadState() {
  const raw = fs.readFileSync(STATE_PATH, 'utf8');
  return JSON.parse(raw);
}

function saveState(state) {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + '\n', 'utf8');
}

export { loadState, saveState, STATE_PATH };
