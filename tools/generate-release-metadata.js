#!/usr/bin/env node
/* eslint-disable no-console */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const version = process.argv[2];
if (!version) {
  console.error('Usage: node tools/generate-release-metadata.js <version>');
  process.exit(1);
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '..');
const outDir = path.join(repoRoot, 'out');
const releaseDir = path.join(outDir, 'releases', `v${version}`);

const ensureDir = (dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
};

ensureDir(releaseDir);

const readJson = (file) => {
  if (!fs.existsSync(file)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(file, 'utf-8'));
};

const dashboard = readJson(path.join(repoRoot, 'pulse_dashboard', 'data', 'dashboard.json')) || {};
const history = Array.isArray(dashboard?.amplify?.history) ? dashboard.amplify.history : [];
const sloSource = history.length > 0 ? history[history.length - 1] : null;
const sloStats = sloSource
  ? {
      cycle: sloSource.cycle,
      commit: sloSource.commit_sha,
      metrics: sloSource.metrics,
    }
  : {};

const testMetrics = readJson(path.join(outDir, 'test-metrics.json')) || { runs: [], summary: {} };
const testMetricsSource = path.join(outDir, 'test-metrics.json');

const listFiles = (dir, predicate = () => true) => {
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs
    .readdirSync(dir)
    .map((file) => path.join(dir, file))
    .flatMap((file) => {
      const stat = fs.statSync(file);
      if (stat.isDirectory()) {
        return listFiles(file, predicate);
      }
      return predicate(file) ? [file] : [];
    });
};

const sboms = fs
  .readdirSync(repoRoot)
  .filter((file) => file.toLowerCase().startsWith('sbom-') && file.endsWith('.json'))
  .map((file) => path.join(repoRoot, file));
const cosignAttestations = listFiles(path.join(repoRoot, 'attestations'), (file) => file.endsWith('.jsonld'));
const provenanceFile = path.join(repoRoot, 'RELEASE_PROVENANCE.json');
const dashboards = [path.join(repoRoot, 'pulse_dashboard', 'public'), path.join(repoRoot, 'pulse_dashboard', 'builder.py')].filter((target) => fs.existsSync(target));
const siteBundle = path.join(repoRoot, 'build');

const artifactSources = {
  docker: path.join(outDir, 'docker'),
  helm: path.join(outDir, 'helm'),
  sdk: path.join(outDir, 'sdk'),
};

Object.entries(artifactSources).forEach(([key, sourceDir]) => {
  const destination = path.join(releaseDir, key);
  if (!fs.existsSync(sourceDir)) {
    return;
  }
  ensureDir(destination);
  listFiles(sourceDir).forEach((file) => {
    const relative = path.relative(sourceDir, file);
    const target = path.join(destination, relative);
    ensureDir(path.dirname(target));
    fs.copyFileSync(file, target);
  });
});

const copyTargets = (files, key) =>
  files
    .filter((file) => fs.existsSync(file))
    .map((file) => {
      const target = path.join(releaseDir, key, path.basename(file));
      ensureDir(path.dirname(target));
      const stat = fs.statSync(file);
      if (stat.isDirectory()) {
        return null;
      }
      fs.copyFileSync(file, target);
      return target;
    })
    .filter(Boolean);

const sbomCopies = copyTargets(sboms, 'sbom');
const attestationCopies = copyTargets(cosignAttestations, 'attestations');
const provenanceCopies = copyTargets([provenanceFile], 'provenance');
const dashboardCopies = dashboards.flatMap((item) => {
  if (!fs.existsSync(item)) {
    return [];
  }
  const destination = path.join(releaseDir, 'dashboards', path.basename(item));
  if (fs.statSync(item).isDirectory()) {
    ensureDir(destination);
    listFiles(item).forEach((file) => {
      const rel = path.relative(item, file);
      const target = path.join(destination, rel);
      ensureDir(path.dirname(target));
      fs.copyFileSync(file, target);
    });
    return [destination];
  }
  ensureDir(path.dirname(destination));
  fs.copyFileSync(item, destination);
  return [destination];
});

if (fs.existsSync(siteBundle)) {
  const target = path.join(releaseDir, 'site');
  ensureDir(target);
  listFiles(siteBundle).forEach((file) => {
    const rel = path.relative(siteBundle, file);
    const dest = path.join(target, rel);
    ensureDir(path.dirname(dest));
    fs.copyFileSync(file, dest);
  });
}

const metadata = {
  version,
  generatedAt: new Date().toISOString(),
  slo: sloStats,
  tests: testMetrics,
  artifacts: {
    docker: listFiles(path.join(releaseDir, 'docker')),
    helm: listFiles(path.join(releaseDir, 'helm')),
    sdk: listFiles(path.join(releaseDir, 'sdk')),
  },
  sboms: sbomCopies,
  cosignAttestations: attestationCopies,
  provenance: provenanceCopies,
  dashboards: dashboardCopies,
  siteBundle: fs.existsSync(path.join(releaseDir, 'site')) ? path.join(releaseDir, 'site') : null,
};

const metadataFile = path.join(releaseDir, 'metadata.json');
fs.writeFileSync(metadataFile, `${JSON.stringify(metadata, null, 2)}\n`);

if (fs.existsSync(testMetricsSource)) {
  fs.copyFileSync(testMetricsSource, path.join(releaseDir, 'test-metrics.json'));
}

const changelogPath = path.join(repoRoot, 'CHANGELOG.md');
let changelogNotes = '';
if (fs.existsSync(changelogPath)) {
  const changelog = fs.readFileSync(changelogPath, 'utf-8');
  const pattern = new RegExp(`#\\s*${version.replace(/\./g, '\\.')}(?:.|\n)*?(?=\n#|$)`);
  const match = changelog.match(pattern);
  changelogNotes = match ? match[0].trim() : '';
}

if (changelogNotes) {
  fs.writeFileSync(path.join(releaseDir, 'CHANGELOG.md'), `${changelogNotes}\n`);
}

const releaseNotes = `# EchoEvolver v${version} Release\n\n` +
  `## Service-Level Objectives\n${JSON.stringify(sloStats, null, 2)}\n\n` +
  `## Test Summary\n${JSON.stringify(testMetrics.summary, null, 2)}\n`;

fs.writeFileSync(path.join(releaseDir, 'RELEASE_NOTES.md'), `${releaseNotes}\n`);

console.log(`Prepared release metadata in ${releaseDir}`);
