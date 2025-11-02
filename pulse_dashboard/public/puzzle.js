const form = document.getElementById('puzzleForm');
const input = document.getElementById('puzzleId');
const statusEl = document.getElementById('puzzleStatus');
const metaEl = document.getElementById('puzzleMeta');
const attestationList = document.getElementById('attestationList');

function renderMeta(data) {
  metaEl.innerHTML = '';
  const title = document.createElement('div');
  title.innerHTML = `<strong>Title</strong>${data.title}`;
  const address = document.createElement('div');
  address.innerHTML = `<strong>Address</strong>${data.address || 'None recorded'}`;
  const sha = document.createElement('div');
  sha.innerHTML = `<strong>SHA-256</strong>${data.sha256}`;
  const path = document.createElement('div');
  path.innerHTML = `<strong>Path</strong>${data.path}`;

  metaEl.appendChild(title);
  metaEl.appendChild(address);
  metaEl.appendChild(sha);
  metaEl.appendChild(path);
  metaEl.hidden = false;
}

function renderAttestations(attestations) {
  attestationList.innerHTML = '';
  if (!attestations.length) {
    const empty = document.createElement('li');
    empty.className = 'codex-entry codex-empty';
    empty.textContent = 'No attestations recorded yet. Run the assistant to create one.';
    attestationList.appendChild(empty);
    return;
  }
  attestations.forEach((record) => {
    const item = document.createElement('li');
    item.className = 'codex-entry';

    const header = document.createElement('div');
    header.className = 'codex-entry__header';

    const hash = document.createElement('code');
    hash.className = 'codex-entry__hash';
    hash.textContent = record.record_hash;

    const timestamp = document.createElement('time');
    timestamp.className = 'codex-entry__time';
    timestamp.dateTime = record.ts;
    timestamp.textContent = new Date(record.ts).toLocaleString();

    header.appendChild(hash);
    header.appendChild(timestamp);

    const payload = document.createElement('pre');
    payload.textContent = JSON.stringify(record.payload, null, 2);

    const checksum = document.createElement('p');
    checksum.className = 'codex-entry__summary';
    checksum.textContent = `Checksum: ${record.checksum}`;

    const base58 = document.createElement('p');
    base58.className = 'codex-entry__summary';
    base58.textContent = `Base58: ${record.base58}`;

    item.appendChild(header);
    item.appendChild(payload);
    item.appendChild(checksum);
    item.appendChild(base58);

    attestationList.appendChild(item);
  });
}

async function loadPuzzle(puzzleId) {
  statusEl.textContent = `Loading puzzle ${puzzleId}…`;
  try {
    const response = await fetch(`/api/puzzles/${puzzleId}`);
    if (!response.ok) {
      throw new Error(`Puzzle ${puzzleId} not found`);
    }
    const data = await response.json();
    renderMeta(data);
    renderAttestations(data.attestations || []);
    statusEl.textContent = `Puzzle ${puzzleId} loaded.`;
    const url = new URL(window.location.href);
    url.searchParams.set('id', puzzleId);
    window.history.replaceState({}, '', url);
  } catch (error) {
    statusEl.textContent = error.message;
    metaEl.hidden = true;
    const errorItem = document.createElement('li');
    errorItem.className = 'codex-entry codex-empty';
    errorItem.textContent = 'Unable to load puzzle details.';
    attestationList.innerHTML = '';
    attestationList.appendChild(errorItem);
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const puzzleId = parseInt(input.value, 10);
  if (Number.isNaN(puzzleId) || puzzleId <= 0) {
    statusEl.textContent = 'Enter a valid puzzle identifier.';
    return;
  }
  loadPuzzle(puzzleId);
});

document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const id = parseInt(params.get('id') || '', 10);
  if (!Number.isNaN(id) && id > 0) {
    input.value = id;
    loadPuzzle(id);
  }
});
