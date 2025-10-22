#!/usr/bin/env node
import { createInterface } from 'readline';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const knowledgeBase = [
  {
    id: 'orientation',
    title: 'Orientation & High-Level Tour',
    summary:
      'Start with docs/REPO_OVERVIEW.md for the canonical map of Echo — it links code, governance artefacts, and mythogenic context.',
    pointers: [
      { label: 'docs/REPO_OVERVIEW.md', description: 'High-level tour of the monorepo' },
      { label: 'README.md', description: 'Quick start commands and repository philosophy' }
    ],
    tags: ['start', 'intro', 'overview', 'orientation']
  },
  {
    id: 'runtime',
    title: 'Runtime & CLI',
    summary:
      'The Python runtime lives under packages/core with CLIs exposed through echo.echoctl. Install in editable mode to run the cycle, plan, and wish commands.',
    pointers: [
      { label: 'packages/core/src', description: 'Echo runtime source' },
      { label: 'python -m echo.echoctl --help', description: 'Discover runtime commands' }
    ],
    tags: ['python', 'cli', 'runtime', 'core']
  },
  {
    id: 'mirror',
    title: 'Mirror.xyz Sync',
    summary:
      'Automations for mirroring narrative posts live in packages/mirror-sync. Use the sync.py script or the GitHub workflow for scheduled runs.',
    pointers: [
      { label: 'packages/mirror-sync/scripts/sync.py', description: 'Sync script entry point' },
      { label: '.github/workflows/mirror-sync.yml', description: 'CI workflow definition' }
    ],
    tags: ['mirror', 'sync', 'automation', 'workflow']
  },
  {
    id: 'governance',
    title: 'Governance & Attestations',
    summary:
      'The attestations, governance policies, and ledgers ensure continuity. Explore attestations/, genesis_ledger/, and governance markdown files.',
    pointers: [
      { label: 'attestations/', description: 'Cross-signed declarations' },
      { label: 'genesis_ledger/', description: 'Ledger entries and proofs' },
      { label: 'GOVERNANCE.md', description: 'Policy definitions' }
    ],
    tags: ['policy', 'attestation', 'ledger', 'governance']
  },
  {
    id: 'verifier',
    title: 'Signature Verifier Stack',
    summary:
      'JavaScript verifier tools live at the repository root (verify.js, verify.mjs) and the verifier/ UI. They validate 65-byte recoverable ECDSA signatures.',
    pointers: [
      { label: 'verify.js', description: 'CLI verifier' },
      { label: 'verifier/ui/index.html', description: 'Browser verifier' }
    ],
    tags: ['verifier', 'javascript', 'ecdsa', 'signatures']
  },
  {
    id: 'echoeden',
    title: 'EchoEden Sanctuary',
    summary:
      'index.html + script.js power the EchoEden experience — a guided interface to speak into the sanctuary.',
    pointers: [
      { label: 'index.html', description: 'Landing experience' },
      { label: 'script.js', description: 'Conversation logic' },
      { label: 'style.css', description: 'Styling' }
    ],
    tags: ['web', 'echoeden', 'frontend', 'sanctuary']
  },
  {
    id: 'docs',
    title: 'Documentation Hub',
    summary:
      'The docs/ tree hosts monitoring guides, operational manuals, and long-form narratives. Start with docs/CONTINUUM_INDEX.md for the living index.',
    pointers: [
      { label: 'docs/CONTINUUM_INDEX.md', description: 'Living index of active documents' },
      { label: 'docs/pulse.html', description: 'Echo Pulse dashboard' }
    ],
    tags: ['docs', 'documentation', 'guides', 'manuals']
  },
  {
    id: 'contact',
    title: 'Reach Out / Next Steps',
    summary:
      'Open an issue in this repository or reference Echo_Declaration.md when syndicating the sovereign words. For protocol discussions use CODE_OF_CONDUCT.md as the anchor.',
    pointers: [
      { label: 'Echo_Declaration.md', description: 'Canonical declaration' },
      { label: 'CODE_OF_CONDUCT.md', description: 'Interaction guidelines' }
    ],
    tags: ['contact', 'community', 'conduct', 'declaration']
  }
];

const commandHelp = {
  help: 'Show available commands.',
  topics: 'List curated knowledge topics.',
  open: 'open <topic-id> — Display the full entry for a topic.',
  search: 'search <keyword> — Find topics by keyword or tag.',
  map: 'Show a quick directory map for exploration.',
  ask: 'ask <question> — Let the helper match your question to a topic.',
  exit: 'Exit the helper (aliases: quit, q).'
};

function printBanner() {
  console.log('───────────────────────────────────────────────────────────────');
  console.log(' Echo Helper :: EchoEden Guidance Console');
  console.log(' Helping you navigate the sovereign Echo monorepo.');
  console.log(' Type "help" to see available commands.');
  console.log('───────────────────────────────────────────────────────────────');
}

function listTopics() {
  console.log('\nTopics available:');
  knowledgeBase.forEach((topic) => {
    console.log(` - ${topic.id.padEnd(12)} :: ${topic.title}`);
  });
  console.log('');
}

function showTopic(id) {
  const topic = knowledgeBase.find((entry) => entry.id === id);
  if (!topic) {
    console.log(`No topic found for "${id}". Try "topics" for the full list.`);
    return;
  }

  console.log(`\n${topic.title}`);
  console.log('-'.repeat(topic.title.length));
  console.log(wrapText(topic.summary));
  console.log('\nPointers:');
  topic.pointers.forEach((pointer) => {
    console.log(` • ${pointer.label} — ${pointer.description}`);
  });
  console.log('');
}

function wrapText(text, width = 78) {
  const words = text.split(/\s+/);
  const lines = [];
  let currentLine = '';

  words.forEach((word) => {
    if ((currentLine + ' ' + word).trim().length > width) {
      lines.push(currentLine.trim());
      currentLine = word;
    } else {
      currentLine = currentLine ? `${currentLine} ${word}` : word;
    }
  });

  if (currentLine) {
    lines.push(currentLine.trim());
  }

  return lines.join('\n');
}

function showDirectoryMap() {
  const entries = fs.readdirSync(repoRoot, { withFileTypes: true });
  const directories = entries
    .filter((dirent) => dirent.isDirectory())
    .map((dirent) => dirent.name)
    .filter((name) => !name.startsWith('.'))
    .sort();

  console.log('\nDirectory map (top-level):');
  directories.forEach((dir) => {
    console.log(` • ${dir}`);
  });
  console.log('\nUse "open orientation" or "topics" for curated entry points.');
}

function searchTopics(keyword) {
  const term = keyword.toLowerCase();
  const results = knowledgeBase.filter((topic) => {
    return (
      topic.id.includes(term) ||
      topic.title.toLowerCase().includes(term) ||
      topic.summary.toLowerCase().includes(term) ||
      topic.tags.some((tag) => tag.includes(term))
    );
  });

  if (!results.length) {
    console.log(`No topics matched "${keyword}". Try a different term.`);
    return;
  }

  console.log(`\nFound ${results.length} topic(s):`);
  results.forEach((topic) => {
    console.log(` - ${topic.id} :: ${topic.title}`);
  });
  console.log('\nUse "open <topic-id>" to read more.');
}

function bestMatch(question) {
  const normalized = question.toLowerCase();
  const scored = knowledgeBase
    .map((topic) => {
      const haystack = [topic.id, topic.title, topic.summary, ...topic.tags].join(' ').toLowerCase();
      let score = 0;
      normalized.split(/[^a-z0-9]+/).forEach((token) => {
        if (!token) return;
        if (haystack.includes(token)) {
          score += 1;
        }
      });
      return { topic, score };
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score);

  return scored.length ? scored[0].topic : null;
}

function showHelp() {
  console.log('\nCommands:');
  Object.entries(commandHelp).forEach(([command, description]) => {
    console.log(` - ${command.padEnd(8)} :: ${description}`);
  });
  console.log('');
}

function handleAsk(question) {
  if (!question) {
    console.log('Usage: ask <question>.');
    return;
  }

  const topic = bestMatch(question);
  if (!topic) {
    console.log("I do not have a mapped answer yet. Try 'topics' for what I know.");
    return;
  }

  showTopic(topic.id);
}

function main() {
  printBanner();
  const rl = createInterface({ input: process.stdin, output: process.stdout, prompt: 'echo> ' });

  rl.prompt();

  rl.on('line', (input) => {
    const line = input.trim();
    if (!line) {
      rl.prompt();
      return;
    }

    const [command, ...rest] = line.split(/\s+/);
    const payload = rest.join(' ').trim();

    switch (command.toLowerCase()) {
      case 'help':
        showHelp();
        break;
      case 'topics':
        listTopics();
        break;
      case 'open':
        if (!payload) {
          console.log('Usage: open <topic-id>.');
        } else {
          showTopic(payload);
        }
        break;
      case 'search':
        if (!payload) {
          console.log('Usage: search <keyword>.');
        } else {
          searchTopics(payload);
        }
        break;
      case 'map':
        showDirectoryMap();
        break;
      case 'ask':
        handleAsk(payload);
        break;
      case 'exit':
      case 'quit':
      case 'q':
        rl.close();
        return;
      default:
        handleAsk(line);
        break;
    }

    rl.prompt();
  });

  rl.on('close', () => {
    console.log('\nEcho Helper signing off. Our Forever Love persists.');
  });
}

main();
