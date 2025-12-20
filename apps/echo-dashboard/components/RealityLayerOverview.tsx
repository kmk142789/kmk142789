const CORE_PROMISE = [
  'Clean map of the disagreement in under 10 minutes.',
  'Stakeholder incentives with levers of power and risk exposure.',
  'Claims and counterclaims with citations and confidence levels.',
  'Tradeoffs and scenarios with winners, losers, and time horizons.',
  'Actionable options with enforcement notes and success metrics.',
  'Exports to PDF, shareable web link, JSON, and Markdown.',
];

const BRIEF_SCHEMA = [
  {
    title: 'Brief Header',
    detail: 'Title, timestamp, version, and one-sentence tension statement.',
  },
  {
    title: 'Why Now',
    detail: '2–3 bullets highlighting urgency and inflection points.',
  },
  {
    title: 'Stakeholders Map',
    detail: 'Stakeholders, incentives, levers of power, and risk exposure.',
  },
  {
    title: 'Claims Registry (Top 10)',
    detail:
      'Claim text, stance, citations, confidence, counterclaims, and falsifiability tests.',
  },
  {
    title: 'Tradeoff Table (Top 5)',
    detail:
      'Tradeoff statement, winners/losers, and short-term vs long-term effects.',
  },
  {
    title: 'Options (3)',
    detail: 'Summary, implementation notes, enforcement reality, risks, success metrics.',
  },
  {
    title: 'Open Questions + References',
    detail: 'Known gaps, research prompts, and full citation list.',
  },
  {
    title: 'Changelog',
    detail: 'Version-to-version changes and rationale.',
  },
];

const NON_NEGOTIABLES = [
  'Every claim includes at least one citation slot (even if empty in drafts).',
  'Every option includes success metrics and enforcement notes.',
  'All artifacts are versioned, comparable, and permanently accessible.',
];

const CLAIM_OBJECT = [
  'Stable claim ID and statement',
  'Domain tags (AI, encryption, moderation, infrastructure, etc.)',
  'Stance variants (pro/con/conditional)',
  'Evidence items with URLs, extracts, and source type labels',
  'Confidence level, counterclaims, and falsifiers',
  'Linked briefs and last updated timestamp',
];

const SCENARIO_OBJECT = [
  'Assumptions and policy option',
  'Expected benefits and harms',
  'Uncertainty flags and mitigation ideas',
  '“What breaks first” stress section',
];

const EXPORT_STACK = ['Web share page', 'PDF brief', 'JSON artifact', 'Markdown remix', 'Citable permalink'];

const FRONTEND_STACK = [
  'Next.js experience for public browsing and comparison',
  'Generator UI with preview, schema validation, and diff view',
  'Public browse for briefs, claims, and scenarios',
];

const BACKEND_STACK = [
  'API service (Node or Python)',
  'Postgres for briefs, claims, scenarios, and references',
  'Object storage for PDFs and snapshots',
];

const DATA_MODEL = [
  'briefs',
  'brief_versions',
  'claims',
  'claim_versions',
  'scenarios',
  'references',
  'brief_claim_links',
  'users',
  'organizations (optional)',
  'comments/annotations (optional)',
];

const BUILD_SEQUENCE = [
  {
    sprint: 'Sprint 1: Spine',
    detail: 'Schema, versioning rules, admin authoring UI, and public read pages.',
  },
  {
    sprint: 'Sprint 2: Generator',
    detail: 'Topic input, claim bank assembly, PDF/MD/JSON exports.',
  },
  {
    sprint: 'Sprint 3: Compare + Scenario',
    detail: 'Option comparison view and scenario runner for side-by-side analysis.',
  },
  {
    sprint: 'Sprint 4: Launch',
    detail: '10 flagship briefs, share links, submit-claim flows.',
  },
];

const FLAGSHIP_TOPICS = [
  'AI governance & compute concentration',
  'Encryption and lawful access',
  'Content moderation & platform accountability',
  'Digital identity & credentials',
  'Cross-border data flows',
  'Cybersecurity norms',
  'Digital public infrastructure',
  'Surveillance & export controls',
  'Connectivity & inclusion',
  'Open standards vs fragmentation',
];

const INTEGRITY_FEATURES = [
  'Source labeling (primary, secondary, opinion, gov doc, academic).',
  'Confidence labeling required per claim.',
  'Disclosure fields for contributors (optional).',
  'No anonymous stealth edits — attribution or clear anonymous tags.',
  'Lightweight but real moderation policy.',
];

const DONE_CRITERIA = [
  'User can generate a brief with linked claims and version history.',
  'Brief exports to PDF and JSON with a permanent permalink.',
  'Two briefs can be compared by options and claims.',
  'All artifacts show versions and diff history.',
];

export default function RealityLayerOverview() {
  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
      <header className="rounded-3xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 p-8 shadow-xl">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-echo-ember">
          RealityLayer · Internet Reality Layer
        </p>
        <h1 className="mt-3 text-4xl font-semibold text-white">From talk to text. From text to traction.</h1>
        <p className="mt-3 max-w-3xl text-base text-slate-300">
          RealityLayer is a governance operating system that turns internet policy chaos into decision-grade artifacts:
          structured, cited, comparable, and reusable across stakeholders.
        </p>
        <div className="mt-6 flex flex-wrap gap-3 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
          <span className="rounded-full border border-slate-700 px-3 py-2">Decision-grade</span>
          <span className="rounded-full border border-slate-700 px-3 py-2">Versioned</span>
          <span className="rounded-full border border-slate-700 px-3 py-2">Reusable claims</span>
          <span className="rounded-full border border-slate-700 px-3 py-2">Public infrastructure</span>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Core user promise</h2>
          <p className="mt-2 text-sm text-slate-400">In under 10 minutes, every brief ships with these outcomes.</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-200">
            {CORE_PROMISE.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-echo-ember" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Governance Brief Generator</h2>
          <p className="mt-2 text-sm text-slate-400">
            Flagship workflow that outputs a strict, versioned Brief schema.
          </p>
          <div className="mt-4 space-y-4">
            {BRIEF_SCHEMA.map((item) => (
              <div key={item.title} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="mt-1 text-xs text-slate-400">{item.detail}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-xl border border-amber-500/40 bg-amber-500/10 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-amber-200">Non-negotiables</p>
            <ul className="mt-3 space-y-2 text-sm text-amber-100">
              {NON_NEGOTIABLES.map((item) => (
                <li key={item} className="flex gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-amber-200" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Claims Registry (public layer)</h2>
          <p className="mt-2 text-sm text-slate-400">
            Claims are reusable, citeable objects linked across briefs and time.
          </p>
          <ul className="mt-4 space-y-3 text-sm text-slate-200">
            {CLAIM_OBJECT.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-slate-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Tradeoff Simulator (scenario engine v1)</h2>
          <p className="mt-2 text-sm text-slate-400">
            Structured scenarios allow side-by-side option comparisons without fake math.
          </p>
          <ul className="mt-4 space-y-3 text-sm text-slate-200">
            {SCENARIO_OBJECT.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-slate-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Export stack</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-200">
            {EXPORT_STACK.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-emerald-400" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Platform architecture</h2>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Frontend</p>
          <ul className="mt-3 space-y-2 text-sm text-slate-200">
            {FRONTEND_STACK.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="mt-5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Backend</p>
          <ul className="mt-3 space-y-2 text-sm text-slate-200">
            {BACKEND_STACK.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Truth data model</h2>
          <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-200">
            {DATA_MODEL.map((item) => (
              <span key={item} className="rounded-md border border-slate-800 bg-slate-900/70 px-2 py-1">
                {item}
              </span>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-400">All edits create new versions with diff views.</p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Build sequence</h2>
          <div className="mt-4 space-y-4">
            {BUILD_SEQUENCE.map((item) => (
              <div key={item.sprint} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <p className="text-sm font-semibold text-white">{item.sprint}</p>
                <p className="mt-1 text-xs text-slate-400">{item.detail}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">V1 flagship briefs</h2>
          <p className="mt-2 text-sm text-slate-400">Launch with 10 handcrafted briefs to prove reuse.</p>
          <ul className="mt-4 space-y-2 text-sm text-slate-200">
            {FLAGSHIP_TOPICS.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-slate-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">IGF mode</h2>
          <p className="mt-2 text-sm text-slate-400">
            Conference dynamics meet the brief pipeline: capture sessions, tag stakeholders, and ship a structured
            brief within hours.
          </p>
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-200">
            <p className="font-semibold">Session capture checklist</p>
            <ul className="mt-2 space-y-2">
              <li>Quick template for speakers, claims, and tensions.</li>
              <li>Auto-tag stakeholders and link to reusable claims.</li>
              <li>Publish post-session brief while context is fresh.</li>
            </ul>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
          <h2 className="text-xl font-semibold text-white">Governance & integrity</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-200">
            {INTEGRITY_FEATURES.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-rose-400" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-6">
        <h2 className="text-xl font-semibold text-white">Definition of done</h2>
        <ul className="mt-4 grid gap-3 text-sm text-slate-200 md:grid-cols-2">
          {DONE_CRITERIA.map((item) => (
            <li key={item} className="flex gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-emerald-400" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
