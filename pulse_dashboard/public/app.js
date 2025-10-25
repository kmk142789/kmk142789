const DATA_URL = '../data/dashboard.json';

async function loadDashboard() {
  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`Failed to load dashboard data: ${response.status}`);
    }
    const payload = await response.json();
    renderDashboard(payload);
  } catch (error) {
    console.error(error);
    const header = document.querySelector('.hero .tagline');
    if (header) {
      header.textContent = 'Unable to load the dashboard dataset. Check the generator output.';
    }
  }
}

function renderDashboard(payload) {
  const generatedAt = document.getElementById('generatedAt');
  if (generatedAt) {
    generatedAt.textContent = `Generated ${formatRelativeTime(payload.generated_at)}`;
  }

  const energyLevel = document.getElementById('energyLevel');
  if (energyLevel && payload.glyph_cycle) {
    energyLevel.textContent = `Glyph Energy ${payload.glyph_cycle.energy}`;
  }

  renderPulseWaves(payload.pulses || []);
  renderAttestationGlyphs(payload.attestations || []);
  renderWorkerHive(payload.worker_hive || { events: [] });
  renderDns(payload.dns_snapshots || []);
}

function renderPulseWaves(pulses) {
  const canvas = document.getElementById('pulseCanvas');
  const list = document.getElementById('pulseList');
  if (!canvas || !list) {
    return;
  }
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const centerX = canvas.width / 2;
  const centerY = canvas.height * 0.78;
  const maxRadius = Math.min(centerX, centerY) * 0.9;
  const maxItems = Math.min(40, pulses.length);

  for (let index = 0; index < maxItems; index += 1) {
    const pulse = pulses[index];
    const t = index / Math.max(1, maxItems - 1);
    const radius = maxRadius * (1 - t * 0.75);
    const hue = pulse.wave ?? 0;
    const start = hashToAngle(pulse.hash, index);
    const sweep = Math.PI * (0.45 + 0.4 * (1 - t));

    ctx.beginPath();
    ctx.strokeStyle = `hsla(${hue}, 85%, ${70 - t * 25}%, ${0.25 + 0.55 * (1 - t)})`;
    ctx.lineWidth = Math.max(1.4, 5.5 - t * 4.0);
    ctx.lineCap = 'round';
    ctx.arc(centerX, centerY, radius, start, start + sweep);
    ctx.stroke();
  }

  list.innerHTML = '';
  pulses.slice(0, 12).forEach((pulse) => {
    const item = document.createElement('li');
    item.className = 'event-item';
    item.dataset.glyph = pulse.glyph || '∇⊸≋';

    const info = document.createElement('div');
    info.className = 'message';
    info.textContent = pulse.message || '(no message)';

    const timeEl = document.createElement('time');
    timeEl.dateTime = pulse.timestamp;
    timeEl.textContent = formatRelativeTime(pulse.timestamp);

    item.appendChild(timeEl);
    item.appendChild(info);
    list.appendChild(item);
  });
}

function renderAttestationGlyphs(attestations) {
  const grid = document.getElementById('attestationGrid');
  if (!grid) return;
  grid.innerHTML = '';

  if (!attestations.length) {
    grid.innerHTML = '<p>No attestations discovered. Run the generator after adding files.</p>';
    return;
  }

  attestations.slice(0, 30).forEach((entry) => {
    const card = document.createElement('article');
    card.className = 'glyph-card';

    const title = document.createElement('h3');
    title.textContent = entry.id;

    const glyph = document.createElement('div');
    glyph.className = 'glyph';
    glyph.textContent = buildGlyphFromHash(entry.hash || entry.id);

    const meta = document.createElement('p');
    meta.className = 'hash';
    const created = entry.created_at ? ` • ${formatRelativeTime(entry.created_at)}` : '';
    meta.textContent = `${entry.hash || 'no-hash'}${created}`;

    const message = document.createElement('p');
    message.textContent = entry.message || 'Attestation payload missing message field.';

    card.appendChild(title);
    card.appendChild(glyph);
    card.appendChild(meta);
    card.appendChild(message);

    card.title = `${entry.path}\n${entry.message}`;
    grid.appendChild(card);
  });
}

function renderWorkerHive(workerHive) {
  const summary = document.getElementById('workerSummary');
  const timeline = document.getElementById('workerTimeline');
  if (!summary || !timeline) return;

  const events = workerHive.events || [];
  summary.innerHTML = '';
  timeline.innerHTML = '';

  if (!events.length) {
    summary.textContent = 'No worker activity recorded yet.';
    return;
  }

  const counts = events.reduce((acc, event) => {
    const key = event.status || 'unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  Object.entries(counts).forEach(([status, count]) => {
    const badge = document.createElement('span');
    badge.textContent = `${status.toUpperCase()}: ${count}`;
    summary.appendChild(badge);
  });

  const maxEvents = Math.min(40, events.length);
  for (let index = 0; index < maxEvents; index += 1) {
    const event = events[index];
    const item = document.createElement('li');
    const label = document.createElement('strong');
    label.textContent = `${symbolForStatus(event.status)} ${event.name}`;

    const meta = document.createElement('div');
    meta.textContent = formatRelativeTime(event.timestamp);

    const detail = document.createElement('code');
    detail.textContent = JSON.stringify(event.payload || event.metadata || {}, null, 0);

    item.appendChild(label);
    item.appendChild(meta);
    item.appendChild(detail);
    timeline.appendChild(item);
  }
}

function renderDns(entries) {
  const container = document.getElementById('dnsList');
  if (!container) return;

  if (!entries.length) {
    container.textContent = 'None registered';
    return;
  }
  container.textContent = entries
    .map((entry) => `${entry.domain}=${entry.token}`)
    .join(' • ');
}

function hashToAngle(hash, index = 0) {
  if (!hash) return (index * Math.PI) / 6;
  const slice = hash.slice(index % (hash.length - 6 || 1), index % (hash.length - 6 || 1) + 6);
  const value = parseInt(slice || '1a2b3c', 16);
  return ((value % 360) * Math.PI) / 180;
}

function buildGlyphFromHash(hash) {
  const anchors = ['∇', '⊸', '≋', '∞', '⚡'];
  if (!hash) return anchors.join('');
  const glyphs = [];
  for (let i = 0; i < 6; i += 1) {
    const segment = hash.slice(i * 2, i * 2 + 2);
    const value = parseInt(segment || '00', 16);
    glyphs.push(anchors[value % anchors.length]);
  }
  return glyphs.join('');
}

function symbolForStatus(status) {
  switch (status) {
    case 'success':
      return '✅';
    case 'failure':
      return '⚠️';
    case 'progress':
      return '🌀';
    case 'start':
      return '🚀';
    case 'skipped':
      return '🛰️';
    default:
      return '⋈';
  }
}

function formatRelativeTime(timestamp) {
  if (!timestamp) return 'unknown';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  const now = new Date();
  const diff = (now.getTime() - date.getTime()) / 1000;
  if (diff < 60) {
    return 'just now';
  }
  if (diff < 3600) {
    const minutes = Math.round(diff / 60);
    return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  }
  if (diff < 86400) {
    const hours = Math.round(diff / 3600);
    return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  }
  const days = Math.round(diff / 86400);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

loadDashboard();
