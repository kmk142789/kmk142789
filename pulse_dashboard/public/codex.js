const API_BASE = '/api/codex';

const generatedEl = document.getElementById('codexGenerated');
const countEl = document.getElementById('codexCount');
const timelineEl = document.getElementById('codexTimeline');
const labelFilter = document.getElementById('labelFilter');
const startDate = document.getElementById('startDate');
const endDate = document.getElementById('endDate');
const limitInput = document.getElementById('entryLimit');
const filterForm = document.getElementById('codexFilters');
const resetButton = document.getElementById('resetFilters');

async function fetchJSON(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function isoFromDateInput(value, endOfDay = false) {
  if (!value) return null;
  const suffix = endOfDay ? 'T23:59:59Z' : 'T00:00:00Z';
  return `${value}${suffix}`;
}

function buildTimelineItem(item) {
  const entry = document.createElement('li');
  entry.className = 'codex-entry';

  const header = document.createElement('div');
  header.className = 'codex-entry__header';

  const title = document.createElement('a');
  title.className = 'codex-entry__title';
  title.textContent = `#${item.id} · ${item.title}`;
  title.href = item.url;
  title.target = '_blank';
  title.rel = 'noreferrer noopener';

  const merged = document.createElement('time');
  merged.className = 'codex-entry__time';
  merged.dateTime = item.merged_at;
  merged.textContent = item.merged_at ? new Date(item.merged_at).toLocaleString() : 'Unknown';

  header.appendChild(title);
  header.appendChild(merged);

  const summary = document.createElement('p');
  summary.className = 'codex-entry__summary';
  summary.textContent = item.summary || 'No summary provided.';

  const tags = document.createElement('ul');
  tags.className = 'codex-entry__labels';
  (item.labels || []).forEach((label) => {
    const badge = document.createElement('li');
    badge.textContent = label;
    tags.appendChild(badge);
  });

  const commit = document.createElement('code');
  commit.className = 'codex-entry__hash';
  commit.textContent = item.hash || '';

  entry.appendChild(header);
  entry.appendChild(summary);
  entry.appendChild(tags);
  if (item.hash) {
    entry.appendChild(commit);
  }
  return entry;
}

function renderTimeline(items, total, generatedAt) {
  timelineEl.innerHTML = '';
  if (!items.length) {
    const empty = document.createElement('li');
    empty.className = 'codex-entry codex-empty';
    empty.textContent = 'No registry entries match the current filters.';
    timelineEl.appendChild(empty);
  } else {
    items.forEach((item) => {
      timelineEl.appendChild(buildTimelineItem(item));
    });
  }
  generatedEl.textContent = generatedAt ? `Generated ${new Date(generatedAt).toLocaleString()}` : 'Generated at unknown time';
  countEl.textContent = `${items.length} of ${total} entries`;
}

async function loadLabels() {
  try {
    const data = await fetchJSON(`${API_BASE}/labels`);
    const labels = data.labels || [];
    labelFilter.innerHTML = '<option value="">All labels</option>';
    labels.forEach((label) => {
      const option = document.createElement('option');
      option.value = label;
      option.textContent = label;
      labelFilter.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load labels', error);
  }
}

async function loadRegistry(event) {
  if (event) event.preventDefault();
  const params = new URLSearchParams();
  const label = labelFilter.value;
  const start = isoFromDateInput(startDate.value, false);
  const end = isoFromDateInput(endDate.value, true);
  const limit = parseInt(limitInput.value, 10);
  if (label) params.set('label', label);
  if (start) params.set('since', start);
  if (end) params.set('until', end);
  if (!Number.isNaN(limit) && limit > 0) params.set('limit', String(limit));

  try {
    timelineEl.classList.add('loading');
    const data = await fetchJSON(`${API_BASE}?${params.toString()}`);
    renderTimeline(data.items || [], data.total_items || 0, data.generated_at);
  } catch (error) {
    console.error('Unable to load registry', error);
    const errorItem = document.createElement('li');
    errorItem.className = 'codex-entry codex-empty';
    errorItem.textContent = 'Unable to fetch registry data.';
    timelineEl.innerHTML = '';
    timelineEl.appendChild(errorItem);
  } finally {
    timelineEl.classList.remove('loading');
  }
}

function resetFilters() {
  labelFilter.value = '';
  startDate.value = '';
  endDate.value = '';
  limitInput.value = '40';
  loadRegistry();
}

filterForm.addEventListener('submit', loadRegistry);
resetButton.addEventListener('click', resetFilters);

document.addEventListener('DOMContentLoaded', async () => {
  await loadLabels();
  await loadRegistry();
});
