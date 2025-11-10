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
  renderTransparency(payload);
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

function renderTransparency(payload) {
  const container = document.getElementById('transparencyGrid');
  if (!container) return;
  container.innerHTML = '';

  const amplifyCard = buildAmplifyCard(payload.amplify || {});
  const proofCard = buildProofCard(payload.proof_of_computation || {});
  const impactCard = buildImpactCard(payload.impact_explorer || {});

  [amplifyCard, proofCard, impactCard].forEach((card) => {
    if (card) {
      container.appendChild(card);
    }
  });
}

function buildAmplifyCard(amplify) {
  const card = createTransparencyCard(
    'Amplify Oversight',
    'Latest cycle momentum and health from the Amplify operator log.'
  );

  const summary = amplify.summary || {};
  const latest = amplify.latest || {};
  const stats = document.createElement('dl');
  stats.className = 'stat-list';

  appendStat(stats, 'Presence', summary.presence || 'No activity recorded');
  appendStat(stats, 'Cycles tracked', formatNumber(summary.cycles_tracked));
  if (typeof summary.average_index === 'number') {
    appendStat(stats, 'Average index', summary.average_index.toFixed(2));
  }
  if (typeof summary.peak_index === 'number') {
    appendStat(stats, 'Peak index', summary.peak_index.toFixed(2));
  }
  if (typeof summary.momentum === 'number') {
    const symbol = summary.momentum >= 0 ? '+' : '−';
    appendStat(stats, 'Momentum', `${symbol}${Math.abs(summary.momentum).toFixed(2)}`);
  }
  card.appendChild(stats);

  const metrics = latest.metrics || {};
  const metricEntries = Object.entries(metrics).filter(([, value]) => value !== undefined);
  if (metricEntries.length) {
    const list = document.createElement('ul');
    list.className = 'metric-list';
    metricEntries.slice(0, 6).forEach(([key, value]) => {
      const item = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = key.replace(/_/g, ' ');
      const metricValue = document.createElement('strong');
      metricValue.textContent = typeof value === 'number' ? value.toFixed(2) : String(value);
      item.appendChild(label);
      item.appendChild(metricValue);
      list.appendChild(item);
    });
    card.appendChild(list);
  }

  if (summary.latest_commit) {
    const footer = document.createElement('p');
    footer.className = 'footnote';
    footer.textContent = `Latest commit ${truncateHash(summary.latest_commit)}`;
    card.appendChild(footer);
  }

  return card;
}

function buildProofCard(proof) {
  const card = createTransparencyCard(
    'Proof-of-Computation',
    'Verification ledger for puzzle proofs and submission receipts.'
  );

  const stats = document.createElement('dl');
  stats.className = 'stat-list';
  appendStat(stats, 'Records', formatNumber(proof.total));

  const latest = proof.latest || {};
  if (latest.recorded_at) {
    appendStat(stats, 'Latest entry', formatRelativeTime(latest.recorded_at));
  }
  if (latest.puzzle !== undefined) {
    appendStat(stats, 'Puzzle', latest.puzzle);
  }
  if (latest.mode) {
    appendStat(stats, 'Mode', latest.mode);
  }
  card.appendChild(stats);

  const records = Array.isArray(proof.records) ? proof.records : [];
  if (records.length) {
    const log = document.createElement('ul');
    log.className = 'log-list';
    records.slice(0, 4).forEach((record) => {
      const item = document.createElement('li');
      const header = document.createElement('strong');
      const titleParts = [];
      if (record.puzzle !== undefined) {
        titleParts.push(`Puzzle ${record.puzzle}`);
      }
      if (record.mode) {
        titleParts.push(String(record.mode));
      }
      header.textContent = titleParts.join(' • ') || 'Ledger entry';

      const meta = document.createElement('span');
      if (record.recorded_at) {
        meta.textContent = formatRelativeTime(record.recorded_at);
      } else if (record.submitted_at) {
        meta.textContent = formatRelativeTime(record.submitted_at);
      }

      const digest = document.createElement('code');
      if (record.digest) {
        digest.textContent = truncateHash(record.digest, 18);
      } else if (record.tx_hash) {
        digest.textContent = truncateHash(record.tx_hash, 18);
      }

      item.appendChild(header);
      if (meta.textContent) {
        item.appendChild(meta);
      }
      if (digest.textContent) {
        item.appendChild(digest);
      }
      log.appendChild(item);
    });
    card.appendChild(log);
  }

  return card;
}

function buildImpactCard(impact) {
  const card = createTransparencyCard(
    'Treasury Transparency',
    'Latest cash flows powering childcare cooperatives and mutual aid.'
  );

  const financials = impact.financials || {};
  const totals = financials.totals || {};
  const rolling = financials.rolling_30_days || {};

  const stats = document.createElement('dl');
  stats.className = 'stat-list';
  appendStat(stats, 'Donations', formatCurrency(totals.donations));
  appendStat(stats, 'Disbursed', formatCurrency(totals.disbursed));
  appendStat(stats, 'Balance', formatCurrency(totals.balance));
  appendStat(stats, '30-day donations', formatCurrency(rolling.donations));
  appendStat(stats, '30-day disbursed', formatCurrency(rolling.disbursed));
  card.appendChild(stats);

  const events = Array.isArray(financials.events) ? financials.events : [];
  if (events.length) {
    const log = document.createElement('ul');
    log.className = 'log-list';
    events.slice(0, 4).forEach((event) => {
      const item = document.createElement('li');
      const header = document.createElement('strong');
      const action = event.type === 'donation' ? 'Donation' : 'Disbursement';
      header.textContent = `${action} • ${formatCurrency(event.amount_usd)}`;

      const meta = document.createElement('span');
      const details = [];
      if (event.source) details.push(event.source);
      if (event.beneficiary) details.push(event.beneficiary);
      if (event.timestamp) details.push(formatRelativeTime(event.timestamp));
      meta.textContent = details.join(' • ');

      const memo = document.createElement('code');
      if (event.memo) {
        memo.textContent = event.memo;
      } else if (event.tx_hash) {
        memo.textContent = truncateHash(event.tx_hash, 18);
      }

      item.appendChild(header);
      if (meta.textContent) {
        item.appendChild(meta);
      }
      if (memo.textContent) {
        item.appendChild(memo);
      }
      log.appendChild(item);
    });
    card.appendChild(log);
  }

  return card;
}

function createTransparencyCard(title, description) {
  const card = document.createElement('article');
  card.className = 'transparency-card';
  const heading = document.createElement('h3');
  heading.textContent = title;
  card.appendChild(heading);

  if (description) {
    const desc = document.createElement('p');
    desc.className = 'description';
    desc.textContent = description;
    card.appendChild(desc);
  }
  return card;
}

function appendStat(container, label, value) {
  if (value === undefined || value === null || value === '') return;
  const dt = document.createElement('dt');
  dt.textContent = label;
  const dd = document.createElement('dd');
  dd.textContent = typeof value === 'number' ? formatNumber(value) : String(value);
  container.appendChild(dt);
  container.appendChild(dd);
}

function truncateHash(hash, length = 12) {
  if (!hash || typeof hash !== 'string') return '';
  if (hash.length <= length) return hash;
  const prefix = hash.slice(0, Math.max(4, Math.floor(length / 2)));
  const suffix = hash.slice(-Math.max(4, Math.floor(length / 2)));
  return `${prefix}…${suffix}`;
}

function formatNumber(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }
  return value.toLocaleString('en-US');
}

function formatCurrency(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
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
