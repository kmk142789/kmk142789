import express from 'express';
import cors from 'cors';

import { resolveDid } from './lib/did_resolver.js';
import { issueVerifiableCredential } from './lib/vc_issuer.js';
import { loadState } from './lib/relief_ledger.js';
import { getStatus, runEvolution } from './echo_evolve.js';

const app = express();
const PORT = process.env.PORT || 4001;

app.use(cors());
app.use(express.json());

function requireGuardian(req, res, next) {
  try {
    const state = loadState();
    const guardianId = req.header('x-guardian-id');
    const guardianToken = req.header('x-guardian-token') || req.header('authorization');

    if (!guardianToken) {
      return res.status(403).json({ error: 'Guardian authentication required' });
    }

    const guardian = state.guardians?.find(
      (g) => g.auth_token === guardianToken && (!guardianId || g.id === guardianId)
    );

    if (!guardian) {
      return res.status(403).json({ error: 'Guardian authentication required' });
    }

    req.guardian = guardian;
    next();
  } catch (err) {
    res.status(500).json({ error: 'Guardian check failed', detail: err.message });
  }
}

app.get('/did/resolve/:did', (req, res) => {
  const did = decodeURIComponent(req.params.did);
  const resolved = resolveDid(did);
  if (resolved) return res.json(resolved);
  res.status(404).json({ error: 'DID Not Found' });
});

app.get('/vc/issue/:event_id', requireGuardian, (req, res) => {
  try {
    const state = loadState();
    const event = state.relief_ledger?.find((e) => e.id === req.params.event_id);

    if (!event) return res.status(404).json({ error: 'Event Not Found' });

    const vc = issueVerifiableCredential(event);
    res.json({ ok: true, vc });
  } catch (err) {
    res.status(500).json({ error: 'VC Issuance Failed', detail: err.message });
  }
});

app.get('/echo/status', (_req, res) => {
  try {
    const status = getStatus();
    res.json(status);
  } catch (err) {
    res.status(500).json({ error: 'Status Failed', detail: err.message });
  }
});

app.post('/echo/evolve', requireGuardian, (_req, res) => {
  try {
    const result = runEvolution();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Evolution Failed', detail: err.message });
  }
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Echo node listening on port ${PORT}`);
});
