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
const dashboards = [
  path.join(repoRoot, 'pulse_dashboard', 'public'),
  path.join(repoRoot, 'pulse_dashboard', 'builder.py'),
].filter((target) => fs.existsSync(target));
const siteBundle = path.join(repoRoot, 'build');

const artifactSources = {
  docker: path.join(outDir, 'docker'),
  helm: path.join(outDir, 'helm'),
  sdk: path.join(outDir, 'sdk'),
  publish: path.join(outDir, 'publish'),
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

const toRelative = (files) => files.map((file) => path.relative(repoRoot, file));
const releaseSiteDir = fs.existsSync(path.join(releaseDir, 'site')) ? path.join(releaseDir, 'site') : null;
const artifactInventory = Object.fromEntries(
  Object.keys(artifactSources).map((key) => [key, toRelative(listFiles(path.join(releaseDir, key)))]),
);
const sbomRelatives = toRelative(sbomCopies);
const attestationRelatives = toRelative(attestationCopies);
const provenanceRelatives = toRelative(provenanceCopies);
const dashboardRelatives = toRelative(dashboardCopies);
const siteRelative = releaseSiteDir ? path.relative(repoRoot, releaseSiteDir) : null;
const generatedAt = new Date().toISOString();

const bulletList = (items, indent = 0, fallback = 'None recorded') => {
  const prefix = '  '.repeat(indent);
  if (!items || items.length === 0) {
    return [`${prefix}- ${fallback}`];
  }
  return items.map((item) => `${prefix}- ${item}`);
};

const sloLines = (() => {
  if (!sloStats || Object.keys(sloStats).length === 0) {
    return ['- No SLO snapshot available.'];
  }
  const lines = [`- Cycle ${sloStats.cycle ?? 'n/a'} (commit ${sloStats.commit ?? 'n/a'})`];
  Object.entries(sloStats.metrics || {}).forEach(([metric, value]) => {
    lines.push(`  - ${metric}: ${value}`);
  });
  return lines;
})();

const defaultTestRuns = [
  {
    command: 'python -m pytest --maxfail 1 --disable-warnings',
    cwd: repoRoot,
    status: 'pending',
    totals: { total: 0, passed: 0, failed: 0, skipped: 0 },
  },
  {
    command: 'npm test --silent',
    cwd: repoRoot,
    status: 'pending',
    totals: { total: 0, passed: 0, failed: 0, skipped: 0 },
  },
  {
    command: 'go test ./...',
    cwd: path.join(repoRoot, 'clients', 'go', 'echo_computer_agent_client'),
    status: 'pending',
    totals: { total: 0, passed: 0, failed: 0, skipped: 0 },
  },
];

const recordedRuns = Array.isArray(testMetrics.runs) && testMetrics.runs.length > 0 ? testMetrics.runs : defaultTestRuns;
const computedSummary = testMetrics.summary && Object.keys(testMetrics.summary).length > 0
  ? testMetrics.summary
  : recordedRuns.reduce(
      (acc, run) => {
        const totals = run.totals || {};
        acc.total += totals.total ?? 0;
        acc.passed += totals.passed ?? 0;
        acc.failed += totals.failed ?? 0;
        acc.skipped += totals.skipped ?? 0;
        return acc;
      },
      { total: 0, passed: 0, failed: 0, skipped: 0 },
    );

const testLines = [
  `- Total: ${computedSummary.total} (passed ${computedSummary.passed}, failed ${computedSummary.failed}, skipped ${computedSummary.skipped})`,
  ...recordedRuns.map((run) => {
    const totals = run.totals || {};
    const allZero = ['total', 'passed', 'failed', 'skipped'].every((key) => (totals[key] ?? 0) === 0);
    const status = run.status ? run.status.toLowerCase() : '';
    const descriptor =
      status === 'pending' && allZero
        ? 'pending (awaiting release pipeline)'
        : typeof totals.total === 'number'
            ? `${totals.passed ?? 0}/${totals.total} passed (failed ${totals.failed ?? 0}, skipped ${totals.skipped ?? 0})`
            : run.status ?? 'pending';
    return `  - ${run.command}: ${descriptor}`;
  }),
];

const metadata = {
  version,
  generatedAt,
  slo: sloStats,
  tests: {
    ...testMetrics,
    summary: computedSummary,
    runs: recordedRuns,
  },
  artifacts: artifactInventory,
  sboms: sbomRelatives,
  cosignAttestations: attestationRelatives,
  provenance: provenanceRelatives,
  dashboards: dashboardRelatives,
  siteBundle: siteRelative,
};

const metadataFile = path.join(releaseDir, 'metadata.json');
fs.writeFileSync(metadataFile, `${JSON.stringify(metadata, null, 2)}\n`);

if (fs.existsSync(testMetricsSource)) {
  fs.copyFileSync(testMetricsSource, path.join(releaseDir, 'test-metrics.json'));
}

const supplyChainLines = [
  '- SBOMs:',
  ...bulletList(sbomRelatives, 1, 'None detected'),
  '- Cosign Attestations:',
  ...bulletList(attestationRelatives, 1, 'None attached'),
  '- Provenance:',
  ...bulletList(provenanceRelatives, 1, 'None captured'),
  '- Dashboards:',
  ...bulletList(dashboardRelatives, 1, 'Not included'),
  '- Site bundle:',
  ...bulletList(siteRelative ? [siteRelative] : [], 1, 'Not generated'),
  '- Mock publish logs:',
  ...bulletList(artifactInventory.publish, 1, 'Pending - generated by release workflow'),
];

const changelogPath = path.join(repoRoot, 'CHANGELOG.md');
let releaseEntry = '';
if (fs.existsSync(changelogPath)) {
  let changelog = fs.readFileSync(changelogPath, 'utf-8');
  const versionHeader = `## [${version}]`;
  const startIndex = changelog.indexOf(versionHeader);
  if (startIndex !== -1) {
    const endIndex = changelog.indexOf('\n## [', startIndex + versionHeader.length);
    const entry = endIndex === -1 ? changelog.slice(startIndex) : changelog.slice(startIndex, endIndex);
    const baseEntry = entry.replace(/\n### Observability[\s\S]*$/u, '').trimEnd();
    const enrichedEntry = `${baseEntry}\n\n### Observability\n${sloLines.join('\n')}\n\n### Test Totals\n${testLines.join(
      '\n',
    )}\n\n### Supply Chain Assets\n${supplyChainLines.join('\n')}\n`;
    releaseEntry = enrichedEntry.trim();
    const updatedChangelog =
      changelog.slice(0, startIndex) + enrichedEntry + (endIndex === -1 ? '' : changelog.slice(endIndex));
    changelog = updatedChangelog.trimEnd() + '\n';
    fs.writeFileSync(changelogPath, changelog);
  }
}

if (releaseEntry) {
  fs.writeFileSync(path.join(releaseDir, 'CHANGELOG.md'), `${releaseEntry}\n`);
}

const releaseNotesLines = [
  `# EchoEvolver v${version} Release`,
  '',
  '## Service-Level Objectives',
  ...sloLines,
  '',
  '## Test Summary',
  ...testLines,
  '',
  '## Supply Chain',
  ...supplyChainLines,
];
fs.writeFileSync(path.join(releaseDir, 'RELEASE_NOTES.md'), `${releaseNotesLines.join('\n')}\n`);

const summaryFile = path.join(releaseDir, 'release-summary.json');
const releaseSummary = {
  version,
  generatedAt,
  slo: sloStats,
  testSummary: computedSummary,
  testRuns: recordedRuns.map((run) => ({
    command: run.command,
    cwd: run.cwd,
    status: run.status,
    totals: run.totals || {},
  })),
  supplyChain: {
    sboms: sbomRelatives,
    cosignAttestations: attestationRelatives,
    provenance: provenanceRelatives,
    dashboards: dashboardRelatives,
    site: siteRelative,
  },
  mockPublish: artifactInventory.publish,
};
fs.writeFileSync(summaryFile, `${JSON.stringify(releaseSummary, null, 2)}\n`);

console.log(`Prepared release metadata in ${releaseDir}`);
