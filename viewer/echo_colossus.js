const rootInput = document.querySelector('#root-input');
const searchInput = document.querySelector('#search-input');
const loadButton = document.querySelector('#load-button');
const statusEl = document.querySelector('#status');
const tableBody = document.querySelector('#results tbody');

let dataset = [];

function setStatus(message, kind = 'info') {
  statusEl.textContent = message;
  statusEl.dataset.kind = kind;
}

function render(records) {
  tableBody.innerHTML = '';
  const fragment = document.createDocumentFragment();

  records.forEach((record) => {
    const tr = document.createElement('tr');

    const idCell = document.createElement('td');
    idCell.textContent = record.id;

    const nameCell = document.createElement('td');
    nameCell.textContent = record.name;

    const addressCell = document.createElement('td');
    addressCell.textContent = record.address_base58;

    const hashCell = document.createElement('td');
    hashCell.textContent = record.hash160;

    const linkCell = document.createElement('td');
    const link = document.createElement('a');
    link.href = `${record.root}/` + record.file;
    link.textContent = 'JSON';
    link.setAttribute('target', '_blank');
    linkCell.appendChild(link);

    tr.append(idCell, nameCell, addressCell, hashCell, linkCell);
    fragment.appendChild(tr);
  });

  tableBody.appendChild(fragment);
  setStatus(`Showing ${records.length.toLocaleString()} of ${dataset.length.toLocaleString()} puzzles.`);
}

function applySearch() {
  const query = searchInput.value.trim().toLowerCase();
  if (!query) {
    render(dataset);
    return;
  }

  const filtered = dataset.filter((record) => {
    if (record.id.toString() === query) return true;
    return (
      record.address_base58.toLowerCase().includes(query) ||
      record.hash160.toLowerCase().includes(query) ||
      record.name.toLowerCase().includes(query)
    );
  });
  render(filtered);
}

async function loadIndex() {
  const root = rootInput.value.trim().replace(/\/$/, '') || '.';
  const url = `${root}/build/viewer/puzzles_index.json`;
  setStatus(`Loading index from ${url} ...`);
  tableBody.innerHTML = '';

  try {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    dataset = data.map((entry) => ({ ...entry, root }));
    render(dataset);
  } catch (error) {
    console.error(error);
    dataset = [];
    setStatus(`Failed to load index: ${error.message}`, 'error');
  }
}

loadButton.addEventListener('click', loadIndex);
searchInput.addEventListener('input', () => {
  if (dataset.length === 0) {
    return;
  }
  applySearch();
});

window.addEventListener('DOMContentLoaded', () => {
  setStatus('Waiting for dataset load.');
});
