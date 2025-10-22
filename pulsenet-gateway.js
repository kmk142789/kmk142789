// pulsenet-gateway.js
// Node 18+ (or run with `node`), minimal deps: ws, express, body-parser
import express from "express";
import bodyParser from "body-parser";
import { WebSocketServer } from "ws";
import fs from "fs";

const PORT = process.env.PORT || 8080;
const app = express();
app.use(bodyParser.json());

// In-memory: pulses and the current genesis attestation
let pulses = [];                // {ts, type, summary}
let genesisAtlas = null;        // loaded attestation

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
const pushPulse = (type, summary) => {
  const p = { ts: new Date().toISOString(), type, summary };
  pulses.push(p);
  if (pulses.length > 1000) pulses.shift();
  broadcast({ kind: "pulse", data: p });
};

// REST: ingest an attestation (public JSON artifact)
app.post("/attest/import", (req, res) => {
  const att = req.body;
  if (!att || !att.owner) return res.status(400).send({ error: "bad attest" });
  genesisAtlas = att;
  fs.writeFileSync("./genesis-atlas.json", JSON.stringify(att, null, 2));
  pushPulse("attest_import", `Imported attest for ${att.owner}`);
  return res.send({ status: "ok" });
});

// REST: register simple user (attaches to atlas as registration entry)
app.post("/register", (req, res) => {
  const { name, xpub } = req.body;
  if (!name || !xpub) return res.status(400).send({ error: "name + xpub required" });
  const entry = { name, xpub, ts: new Date().toISOString() };
  if (!genesisAtlas) genesisAtlas = { owner: "unbound", wallets: [] };
  if (!genesisAtlas.wallets) genesisAtlas.wallets = [];
  genesisAtlas.wallets.push(entry);
  fs.writeFileSync("./genesis-atlas.json", JSON.stringify(genesisAtlas, null, 2));
  pushPulse("register", `Registered ${name}`);
  return res.send({ status: "ok", entry });
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
