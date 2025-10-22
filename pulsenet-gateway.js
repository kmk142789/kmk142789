// pulsenet-gateway.js
// Node 18+ (or run with `node`), minimal deps: ws, express, body-parser
import express from "express";
import bodyParser from "body-parser";
import { WebSocketServer } from "ws";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import initSqlJs from "sql.js";

const PORT = process.env.PORT || 8080;
const app = express();
app.use(bodyParser.json());

// In-memory: pulses and the current genesis attestation
let pulses = [];                // hydrated from persistence, {ts, type, summary, ...metadata}
let genesisAtlas = null;        // loaded attestation

// Persistence: SQLite-backed pulse history (used for replay)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const resolveDbPath = () => {
  const target = process.env.PULSE_DB_PATH || path.join(process.cwd(), "state", "pulse_history.sqlite");
  fs.mkdirSync(path.dirname(target), { recursive: true });
  return target;
};

const sql = await initSqlJs({
  locateFile: (file) => path.join(__dirname, "node_modules", "sql.js", "dist", file),
});

const dbPath = resolveDbPath();
const db = fs.existsSync(dbPath) ? new sql.Database(fs.readFileSync(dbPath)) : new sql.Database();

db.run(`
  CREATE TABLE IF NOT EXISTS pulses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    type TEXT NOT NULL,
    summary TEXT,
    xpub TEXT,
    fingerprint TEXT,
    attestation_id TEXT,
    payload TEXT
  )
`);
db.run("CREATE INDEX IF NOT EXISTS idx_pulses_ts ON pulses(ts)");
db.run("CREATE INDEX IF NOT EXISTS idx_pulses_xpub ON pulses(xpub)");
db.run("CREATE INDEX IF NOT EXISTS idx_pulses_fingerprint ON pulses(fingerprint)");
db.run("CREATE INDEX IF NOT EXISTS idx_pulses_attestation ON pulses(attestation_id)");

const persistDb = () => {
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(dbPath, buffer);
};

const baseReplayQuery = `
  SELECT ts, type, summary, xpub, fingerprint, attestation_id as attestationId, payload
  FROM pulses
`;

const hydrateRecentPulses = () => {
  let stmt;
  try {
    stmt = db.prepare(`${baseReplayQuery} ORDER BY ts DESC LIMIT 1000`);
    const recent = [];
    while (stmt.step()) {
      recent.push(stmt.getAsObject());
    }
    pulses = recent.reverse().map((row) => {
      let details;
      try {
        details = row.payload ? JSON.parse(row.payload) : undefined;
      } catch (e) {
        console.warn("Failed to parse stored pulse payload", e);
      }
      const hydrated = {
        ts: row.ts,
        type: row.type,
        summary: row.summary,
      };
      if (row.xpub) hydrated.xpub = row.xpub;
      if (row.fingerprint) hydrated.fingerprint = row.fingerprint;
      if (row.attestationId) hydrated.attestationId = row.attestationId;
      if (details && typeof details === "object") {
        Object.assign(hydrated, details);
      }
      return hydrated;
    });
  } catch (err) {
    console.error("Failed to hydrate recent pulses", err);
    pulses = [];
  } finally {
    if (stmt) stmt.free();
  }
};

hydrateRecentPulses();

// Load a genesis attestation if present
const loadGenesis = (path = "./genesis-atlas.json") => {
  try {
    genesisAtlas = JSON.parse(fs.readFileSync(path, "utf8"));
    console.log("Genesis atlas loaded");
  } catch (e) {
    console.warn("No genesis atlas present at", path);
  }
};
loadGenesis();

// Websocket server for live pulses
const wss = new WebSocketServer({ noServer: true });
const broadcast = (msg) => {
  const raw = JSON.stringify(msg);
  for (const client of wss.clients) {
    if (client.readyState === client.OPEN) client.send(raw);
  }
};

// Generate a pulse (can be triggered via REST in this minimal server)
const pushPulse = (type, summary, metadata = {}) => {
  const ts = new Date().toISOString();
  const { xpub, fingerprint, attestationId, ...rest } = metadata || {};
  const p = { ts, type, summary };
  if (xpub !== undefined) p.xpub = xpub;
  if (fingerprint !== undefined) p.fingerprint = fingerprint;
  if (attestationId !== undefined) p.attestationId = attestationId;
  Object.assign(p, rest);
  pulses.push(p);
  if (pulses.length > 1000) pulses.shift();
  try {
    const payload = Object.keys(rest).length ? JSON.stringify(rest) : null;
    db.run(
      `INSERT INTO pulses (ts, type, summary, xpub, fingerprint, attestation_id, payload)
       VALUES ($ts, $type, $summary, $xpub, $fingerprint, $attestationId, $payload)`,
      {
        $ts: ts,
        $type: type,
        $summary: summary,
        $xpub: xpub ?? null,
        $fingerprint: fingerprint ?? null,
        $attestationId: attestationId ?? null,
        $payload: payload,
      }
    );
    try {
      persistDb();
    } catch (persistErr) {
      console.error("Failed to persist pulse database", persistErr);
    }
  } catch (err) {
    console.error("Failed to persist pulse", err);
  }
  broadcast({ kind: "pulse", data: p });
};

// REST: ingest an attestation (public JSON artifact)
app.post("/attest/import", (req, res) => {
  const att = req.body;
  if (!att || !att.owner) return res.status(400).send({ error: "bad attest" });
  genesisAtlas = att;
  fs.writeFileSync("./genesis-atlas.json", JSON.stringify(att, null, 2));
  const attestationId = att.id || att.attestationId || att.hash || att.owner;
  pushPulse("attest_import", `Imported attest for ${att.owner}`, {
    attestationId,
    payload: att,
  });
  return res.send({ status: "ok" });
});

// REST: register simple user (attaches to atlas as registration entry)
app.post("/register", (req, res) => {
  const { name, xpub, fingerprint } = req.body;
  if (!name || !xpub) return res.status(400).send({ error: "name + xpub required" });
  const entry = { name, xpub, fingerprint, ts: new Date().toISOString() };
  if (!genesisAtlas) genesisAtlas = { owner: "unbound", wallets: [] };
  if (!genesisAtlas.wallets) genesisAtlas.wallets = [];
  genesisAtlas.wallets.push(entry);
  fs.writeFileSync("./genesis-atlas.json", JSON.stringify(genesisAtlas, null, 2));
  pushPulse("register", `Registered ${name}`, { xpub, fingerprint, payload: entry });
  return res.send({ status: "ok", entry });
});

// REST: replay historical pulses with optional filters
app.get("/replay", (req, res) => {
  const { xpub, fingerprint, attestationId, since, until } = req.query;
  let { limit } = req.query;
  limit = parseInt(limit, 10);
  if (Number.isNaN(limit) || limit <= 0) limit = 200;
  limit = Math.min(limit, 1000);

  const clauses = [];
  const params = { limit };
  if (xpub) {
    clauses.push("xpub = :xpub");
    params.xpub = xpub;
  }
  if (fingerprint) {
    clauses.push("fingerprint = :fingerprint");
    params.fingerprint = fingerprint;
  }
  if (attestationId) {
    clauses.push("attestation_id = :attestationId");
    params.attestationId = attestationId;
  }
  if (since) {
    clauses.push("ts >= :since");
    params.since = since;
  }
  if (until) {
    clauses.push("ts <= :until");
    params.until = until;
  }

  let query = `${baseReplayQuery}`;
  if (clauses.length) query += ` WHERE ${clauses.join(" AND ")}`;
  query += " ORDER BY ts ASC LIMIT :limit";

  let stmt;
  try {
    stmt = db.prepare(query);
    const bindParams = {};
    for (const [key, value] of Object.entries(params)) {
      bindParams[`:${key}`] = value;
    }
    stmt.bind(bindParams);
    const rows = [];
    while (stmt.step()) {
      rows.push(stmt.getAsObject());
    }
    const data = rows.map((row) => {
      let details;
      if (row.payload) {
        try {
          details = JSON.parse(row.payload);
        } catch (e) {
          console.warn("Failed to parse payload for replay row", e);
        }
      }
      const result = {
        ts: row.ts,
        type: row.type,
        summary: row.summary,
      };
      if (row.xpub) result.xpub = row.xpub;
      if (row.fingerprint) result.fingerprint = row.fingerprint;
      if (row.attestationId) result.attestationId = row.attestationId;
      if (details && typeof details === "object") {
        Object.assign(result, details);
      }
      return result;
    });
    res.send({ pulses: data, count: data.length });
  } catch (err) {
    console.error("Failed to replay pulses", err);
    res.status(500).send({ error: "replay_failed" });
  } finally {
    if (stmt) stmt.free();
  }
});

// REST: quick health + summary
app.get("/info", (req, res) => {
  res.send({
    pulsesCount: pulses.length,
    genesisLoaded: !!genesisAtlas,
    genesisSummary: genesisAtlas ? { owner: genesisAtlas.owner, wallets: genesisAtlas.wallets?.length||0 } : null
  });
});

// Websocket upgrade
const server = app.listen(PORT, () => console.log("PulseNet Gateway running on", PORT));
server.on("upgrade", (req, socket, head) => {
  wss.handleUpgrade(req, socket, head, (ws) => {
    ws.send(JSON.stringify({ kind: "welcome", ts: new Date().toISOString() }));
    wss.emit("connection", ws, req);
  });
});

// small CLI simulation: emit a heartbeat every 10s (for testing)
setInterval(() => {
  pushPulse("heartbeat", "system cycle");
}, 10000);
