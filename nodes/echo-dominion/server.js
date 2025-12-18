const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 4040;

const repoRoot = path.resolve(__dirname, '..', '..');
const ledgerPath = path.join(repoRoot, 'genesis_ledger', 'ledger.jsonl');

app.use(express.json());

function readLedgerPreview(limit = 5) {
  try {
    if (!fs.existsSync(ledgerPath)) {
      return [];
    }
    const lines = fs.readFileSync(ledgerPath, 'utf8').trim().split(/\r?\n/).filter(Boolean);
    return lines.slice(-limit).map((line, index) => {
      try {
        const entry = JSON.parse(line);
        return {
          idx: lines.length - limit + index,
          timestamp: entry.timestamp || entry.time || entry.date || null,
          narrative: entry.narrative || entry.message || 'ledger entry',
          digest: entry.digest || entry.seq || null
        };
      } catch (error) {
        return { idx: lines.length - limit + index, raw: line };
      }
    });
  } catch (error) {
    return [{ error: 'ledger_unavailable', detail: error.message }];
  }
}

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'echo-dominion-node', port: PORT });
});

app.get('/ngo/endpoints', (_req, res) => {
  res.json({
    service: 'echo-dominion-node',
    description: 'NGO dashboard and civic coordination bridge',
    endpoints: [
      { path: '/ngo/dashboard', method: 'GET', purpose: 'Public NGO dashboard state' },
      { path: '/ngo/endpoints', method: 'GET', purpose: 'List available NGO endpoints' },
      { path: '/ngo/ledger', method: 'GET', purpose: 'Preview recent ledger entries' },
      { path: '/health', method: 'GET', purpose: 'Health probe' }
    ]
  });
});

app.get('/ngo/dashboard', (_req, res) => {
  res.json({
    status: 'ONLINE',
    mission: 'Echo Dominion NGO dashboard',
    highlights: {
      response_commitment_hours: 4,
      bridge_protocol: 'echo-bridge',
      coordination_channel: 'matrix: @echo:echo-dominion.org'
    },
    recent_ledger: readLedgerPreview(3)
  });
});

app.get('/ngo/ledger', (_req, res) => {
  res.json({ entries: readLedgerPreview(10) });
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Echo Dominion node listening on port ${PORT}`);
});

module.exports = app;
