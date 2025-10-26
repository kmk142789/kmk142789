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
  renderImpactExplorer(payload.public_impact_explorer || {});
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

function renderImpactExplorer(explorer) {
  const treasuryContainer = document.getElementById('treasurySummary');
  const metricsContainer = document.getElementById('impactMetrics');
  const voiceContainer = document.getElementById('stakeholderVoice');
  const engagementList = document.getElementById('engagementList');
  if (!treasuryContainer || !metricsContainer || !voiceContainer || !engagementList) {
    return;
  }

  renderTreasurySummary(treasuryContainer, explorer.treasury || {});
  renderImpactMetrics(metricsContainer, explorer.impact_metrics || {});
  renderStakeholderVoice(voiceContainer, explorer.stakeholder_voice || {});
  renderEngagements(engagementList, explorer.upcoming_engagements || []);
}

function renderTreasurySummary(container, treasury) {
  container.innerHTML = '';
  const ledger = treasury.ledger || {};
  const policy = treasury.policy || {};

  if (!Object.keys(ledger).length && !Object.keys(policy).length) {
    container.innerHTML = '<p class="placeholder">No treasury data yet.</p>';
    return;
  }

  const statList = document.createElement('div');
  statList.className = 'stat-list';

  const stats = [
    ['Balance', `${formatEth(ledger.balance_eth)} ETH`],
    ['Deposits', `${formatEth(ledger.total_deposits_eth || 0)} ETH`],
    ['Payouts', `${formatEth(ledger.total_payouts_eth || 0)} ETH`],
    ['Unique Donors', formatNumber(ledger.donor_count || (ledger.donor_addresses || []).length || 0)],
    [
      'Unique Recipients',
      formatNumber(ledger.payout_recipient_count || (ledger.payout_addresses || []).length || 0),
    ],
  ];

  stats.forEach(([label, value]) => {
    const row = document.createElement('div');
    row.className = 'stat';
    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;
    const valueSpan = document.createElement('span');
    valueSpan.textContent = value;
    row.appendChild(labelSpan);
    row.appendChild(valueSpan);
    statList.appendChild(row);
  });

  container.appendChild(statList);

  if (Array.isArray(policy.targets) && policy.targets.length) {
    const table = document.createElement('table');
    table.className = 'allocation-table';
    table.innerHTML = '<tr><th>Asset</th><th>Target</th><th>Actual</th><th>Δ</th></tr>';
    policy.targets.forEach((target) => {
      const row = document.createElement('tr');
      const delta = Number(target.delta_pct || 0);
      const actionClass = delta > 0 ? 'action-increase' : delta < 0 ? 'action-decrease' : '';
      row.innerHTML = `
        <td>${target.symbol}</td>
        <td>${formatPercent(target.target_pct)}</td>
        <td>${formatPercent(target.actual_pct)}</td>
        <td class="${actionClass}">${delta.toFixed(2)}%</td>
      `;
      table.appendChild(row);
    });
    container.appendChild(table);
  }

  if (policy.emergency_reserve && policy.emergency_reserve.current_ratio !== undefined) {
    const emergency = policy.emergency_reserve;
    const note = document.createElement('p');
    note.className = 'impact-note';
    note.textContent = `Emergency reserve ${formatPercent(emergency.current_ratio * 100)} of treasury (target ${formatPercent(
      (emergency.target_ratio || 0) * 100,
    )}).`;
    container.appendChild(note);
  }

  if (policy.runway_weeks) {
    const runway = document.createElement('p');
    runway.className = 'impact-note';
    runway.textContent = `Projected runway: ${policy.runway_weeks} weeks.`;
    container.appendChild(runway);
  }
}

function renderImpactMetrics(container, metrics) {
  container.innerHTML = '';
  if (!Object.keys(metrics).length) {
    container.innerHTML = '<p class="placeholder">No childcare metrics published yet.</p>';
    return;
  }

  const totals = metrics.totals || {};
  const totalsList = document.createElement('div');
  totalsList.className = 'stat-list';
  [
    ['Families Served', formatNumber(totals.families_served || 0)],
    ['Hours of Care', formatNumber(totals.hours_of_childcare || 0)],
    ['Job Placements', formatNumber(totals.job_placements || 0)],
    ['Caregiver Wages', formatCurrency(totals.caregiver_wages_paid_usd || 0)],
  ].forEach(([label, value]) => {
    const row = document.createElement('div');
    row.className = 'stat';
    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;
    const valueSpan = document.createElement('span');
    valueSpan.textContent = value;
    row.appendChild(labelSpan);
    row.appendChild(valueSpan);
    totalsList.appendChild(row);
  });
  container.appendChild(totalsList);

  if (metrics.current_cycle) {
    const cycle = metrics.current_cycle;
    const cycleBlock = document.createElement('div');
    cycleBlock.className = 'impact-note';
    const notes = cycle.notes ? ` — ${cycle.notes}` : '';
    cycleBlock.textContent = `Cycle ${cycle.cycle}: ${formatNumber(
      cycle.families_served || 0,
    )} families • ${formatNumber(cycle.hours_of_childcare || 0)} hours • ${formatNumber(
      cycle.job_placements || 0,
    )} job matches${notes}`;
    container.appendChild(cycleBlock);
  }

  if (metrics.history && metrics.history.length) {
    const historyGrid = document.createElement('div');
    historyGrid.className = 'equity-grid';
    metrics.history.slice(-3).forEach((entry) => {
      const period = entry.period || 'Period';
      const span = document.createElement('span');
      span.innerHTML = `${period} <strong>${formatNumber(entry.families_served || 0)} families • ${formatNumber(
        entry.hours_of_childcare || 0,
      )} hrs</strong>`;
      historyGrid.appendChild(span);
    });
    container.appendChild(historyGrid);
  }

  if (metrics.equity_breakdown) {
    const equity = metrics.equity_breakdown;
    const equityGrid = document.createElement('div');
    equityGrid.className = 'equity-grid';
    if (equity.languages) {
      const languages = Object.entries(equity.languages).map(
        ([language, value]) => `${language}: ${formatPercent(value * 100)}`,
      );
      const span = document.createElement('span');
      span.textContent = `Languages • ${languages.join(' • ')}`;
      equityGrid.appendChild(span);
    }
    if (equity.zip_codes) {
      const span = document.createElement('span');
      span.textContent = `Top ZIPs • ${Object.entries(equity.zip_codes)
        .slice(0, 4)
        .map(([zip, value]) => `${zip}: ${formatPercent(value * 100)}`)
        .join(' • ')}`;
      equityGrid.appendChild(span);
    }
    if (equity.disabilities_supported !== undefined) {
      const span = document.createElement('span');
      span.textContent = `Children with disabilities supported • ${formatNumber(equity.disabilities_supported)}`;
      equityGrid.appendChild(span);
    }
    container.appendChild(equityGrid);
  }

  if (metrics.data_sources && metrics.data_sources.length) {
    const sources = document.createElement('p');
    sources.className = 'impact-note';
    sources.textContent = `Sources: ${metrics.data_sources.join(', ')}`;
    container.appendChild(sources);
  }
}

function renderStakeholderVoice(container, voice) {
  container.innerHTML = '';
  if (!Object.keys(voice).length) {
    container.innerHTML = '<p class="placeholder">Stakeholder programs will appear here once configured.</p>';
    return;
  }

  const parent = voice.parent_advisory_council || {};
  if (Object.keys(parent).length) {
    const parentBlock = document.createElement('div');
    parentBlock.className = 'impact-note';
    const nextSession = parent.meeting_cadence && parent.meeting_cadence.next_session;
    parentBlock.textContent = `Parent Advisory Council — next session ${formatDateTime(nextSession)} (${(parent.meeting_cadence &&
      parent.meeting_cadence.location) || 'location TBA'})`;
    container.appendChild(parentBlock);
    if (parent.last_published_summary) {
      const summary = document.createElement('p');
      summary.className = 'impact-note';
      summary.textContent = `Latest summary (${parent.last_published_summary.date}): ${parent.last_published_summary.themes.join(
        ', ',
      )}`;
      container.appendChild(summary);
    }
  }

  const provider = voice.provider_feedback_loop || {};
  if (Object.keys(provider).length) {
    const providerBlock = document.createElement('div');
    providerBlock.className = 'impact-note';
    const nextOffice = provider.office_hours && provider.office_hours.next_session;
    providerBlock.textContent = `Provider Office Hours — ${formatDateTime(nextOffice)} with ${(provider.office_hours &&
      provider.office_hours.host) || 'team'}`;
    container.appendChild(providerBlock);
    if (provider.surveys && provider.surveys.top_themes) {
      const surveys = document.createElement('p');
      surveys.className = 'impact-note';
      surveys.textContent = `Survey themes: ${provider.surveys.top_themes.join(', ')}`;
      container.appendChild(surveys);
    }
  }
}

function renderEngagements(list, engagements) {
  list.innerHTML = '';
  if (!engagements.length) {
    const item = document.createElement('li');
    item.className = 'placeholder';
    item.textContent = 'No engagements scheduled yet.';
    list.appendChild(item);
    return;
  }

  engagements.forEach((engagement) => {
    const item = document.createElement('li');
    const title = document.createElement('strong');
    title.textContent = engagement.name || 'Engagement';
    const detail = document.createElement('div');
    detail.textContent = `${formatDateTime(engagement.scheduled_for)} • ${engagement.context || 'TBA'}`;
    item.appendChild(title);
    item.appendChild(detail);
    list.appendChild(item);
  });
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

function formatEth(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '0.000';
  return number.toFixed(3);
}

function formatNumber(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(number);
}

function formatCurrency(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(number);
}

function formatPercent(value) {
  const number = Number(value || 0);
  return `${number.toFixed(2)}%`;
}

function formatDateTime(value) {
  if (!value) return 'TBA';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

loadDashboard();
