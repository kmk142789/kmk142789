const express = require("express");
const next = require("next");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const EventEmitter = require("events");

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev, dir: __dirname });
const handle = app.getRequestHandler();
const port = process.env.PORT || 3030;

const repoRoot = path.resolve(__dirname, "..", "..");
const ledgerPath = path.join(repoRoot, "ledger", "little_footsteps_bank.jsonl");
const complianceRegistryPath = path.join(
  repoRoot,
  "legal",
  "legal_posture_registry.jsonl"
);
const proofDir = path.join(repoRoot, "proofs", "little_footsteps_bank");
const puzzlePath = path.join(repoRoot, "puzzle_solutions", "little_footsteps_bank.md");
const governancePath = path.join(repoRoot, "GOVERNANCE.md");

const emitter = new EventEmitter();
let debounceHandle = null;

function scheduleUpdate() {
  if (debounceHandle) {
    clearTimeout(debounceHandle);
  }
  debounceHandle = setTimeout(() => {
    emitter.emit("update");
  }, 250);
}

function safeRead(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return "";
    }
    return fs.readFileSync(filePath, "utf-8");
  } catch (error) {
    console.error("Failed to read", filePath, error);
    return "";
  }
}

function readJsonLines(filePath) {
  const payload = safeRead(filePath);
  if (!payload.trim()) {
    return [];
  }
  return payload
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch (error) {
        console.warn("Skipping malformed line in", filePath, line, error);
        return null;
      }
    })
    .filter(Boolean);
}

function summariseLedger(entries) {
  return entries.map((entry) => ({
    id: String(entry.seq ?? entry.digest ?? entry.timestamp ?? Math.random()),
    timestamp: entry.timestamp ?? "",
    narrative: entry.narrative ?? "",
    amount: entry.amount,
    asset: entry.asset,
    account: entry.account,
    digest: entry.digest,
    classification: entry.compliance?.classification,
    credentialPath: entry.compliance?.credential_path,
    link: (() => {
      const seqNumber = Number(entry.seq);
      if (!Number.isFinite(seqNumber)) {
        return undefined;
      }
      const proofName = `entry_${String(seqNumber).padStart(5, "0")}.json`;
      return path.posix.join("proofs", "little_footsteps_bank", proofName);
    })(),
  }));
}

function readCompliance() {
  const records = readJsonLines(complianceRegistryPath);
  return records.map((record) => ({
    id: `${record.transaction_seq}`,
    timestamp: record.timestamp,
    narrative: `Tx ${record.transaction_seq} classified as ${record.classification}`,
    classification: record.classification,
    credentialPath: record.credential_path,
    digest: record.transaction_digest,
  }));
}

function readGovernance() {
  const body = safeRead(governancePath);
  if (!body) {
    return [];
  }
  return body
    .split(/\n(?=##\s+)/)
    .filter((section) => section.startsWith("##"))
    .slice(0, 6)
    .map((section) => {
      const [titleLine, ...rest] = section.split(/\n/);
      const title = titleLine.replace(/^##\s*/, "").trim();
      const summary = rest.slice(0, 2).join(" ").trim();
      return {
        title,
        summary: summary || "See governance charter for details.",
        reference: title.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        timestamp: new Date().toISOString(),
      };
    });
}

function readAuditTrail() {
  const markdown = safeRead(puzzlePath);
  if (!markdown) {
    return [];
  }
  const sections = markdown.split(/\n(?=##\s+Puzzle)/).filter(Boolean).slice(-5);
  return sections.map((section) => {
    const lines = section.trim().split(/\n/);
    const heading = lines.shift() ?? "Puzzle";
    const detailsLine = lines.find((line) => line.startsWith("* Digest:")) ?? "";
    const proofLine = lines.find((line) => line.startsWith("* Proof bundle:"));
    const timestampMatch = lines.find((line) => line.startsWith("**Account:"));
    return {
      title: heading.replace(/^##\s*/, "").trim(),
      details: detailsLine.replace("* Digest:", "Digest:").trim() || "Ledger addition",
      proofPath: proofLine ? proofLine.replace("* Proof bundle:", "").trim().replace(/`/g, "") : undefined,
      timestamp: timestampMatch ? timestampMatch.replace(/[*`]/g, "").replace("Account:", "").trim() : new Date().toISOString(),
    };
  });
}

function readProofBundles() {
  try {
    if (!fs.existsSync(proofDir)) {
      return [];
    }
    const entries = fs
      .readdirSync(proofDir)
      .filter((name) => name.endsWith(".json"))
      .sort()
      .slice(-20);
    return entries.map((name) => {
      const filePath = path.join(proofDir, name);
      const payload = JSON.parse(safeRead(filePath) || "{}");
      return {
        path: path.relative(repoRoot, filePath),
        digest: payload.digest,
        direction: payload.direction,
        asset: payload.asset,
        otsReceipt: payload.ots_receipt,
      };
    });
  } catch (error) {
    console.error("Unable to read proof bundles", error);
    return [];
  }
}

function collectOpenTimestampLinks(ledgerEntries) {
  const links = [];
  for (const entry of ledgerEntries) {
    if (entry.ots_receipt) {
      links.push({
        label: `Ledger seq ${entry.seq}`,
        path: entry.ots_receipt,
      });
    }
    if (entry.compliance?.ots_receipt) {
      links.push({
        label: `Compliance seq ${entry.seq}`,
        path: entry.compliance.ots_receipt,
      });
    }
  }
  return links;
}

function buildSnapshot() {
  const ledgerEntries = readJsonLines(ledgerPath);
  const inflows = summariseLedger(ledgerEntries.filter((entry) => entry.direction === "inflow")).slice(-10);
  const outflows = summariseLedger(ledgerEntries.filter((entry) => entry.direction === "outflow")).slice(-10);
  const compliance = readCompliance().slice(-10);
  const governance = readGovernance();
  const auditTrail = readAuditTrail();
  const proofBundles = readProofBundles();
  const opentimestamps = collectOpenTimestampLinks(ledgerEntries);

  return {
    updatedAt: new Date().toISOString(),
    inflows: inflows.reverse(),
    outflows: outflows.reverse(),
    compliance: compliance.reverse(),
    governance,
    auditTrail: auditTrail.reverse(),
    proofBundles: proofBundles.reverse(),
    opentimestamps,
  };
}

function watchTarget(targetPath) {
  try {
    const stats = fs.statSync(targetPath);
    if (stats.isDirectory()) {
      fs.watch(targetPath, { persistent: false }, scheduleUpdate);
    } else {
      fs.watch(targetPath, { persistent: false }, scheduleUpdate);
    }
  } catch (error) {
    const parent = path.dirname(targetPath);
    try {
      if (parent && parent !== targetPath) {
        const parentStats = fs.statSync(parent);
        if (parentStats.isDirectory()) {
          fs.watch(parent, { persistent: false }, scheduleUpdate);
        }
      }
    } catch (innerError) {
      // Parent may also be missing; ignore.
    }
  }
}

app.prepare().then(() => {
  const server = express();
  server.use(cors());

  watchTarget(ledgerPath);
  watchTarget(complianceRegistryPath);
  watchTarget(proofDir);
  watchTarget(puzzlePath);
  watchTarget(governancePath);

  server.get("/api/status", (_req, res) => {
    res.json(buildSnapshot());
  });

  server.get("/api/stream", (req, res) => {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    if (typeof res.flushHeaders === "function") {
      res.flushHeaders();
    }

    const send = () => {
      res.write(`data: ${JSON.stringify(buildSnapshot())}\n\n`);
    };

    send();
    const listener = () => send();
    emitter.on("update", listener);
    const keepAlive = setInterval(send, 60000);

    req.on("close", () => {
      clearInterval(keepAlive);
      emitter.removeListener("update", listener);
      res.end();
    });
  });

  server.all("*", (req, res) => handle(req, res));

  server.listen(port, (err) => {
    if (err) throw err;
    console.log(`transparency.bank listening on http://localhost:${port}`);
  });
});
