import fs from 'fs/promises'
import path from 'path'

type Fragment = {
  name: string
  type: string
  slug: string
  last_seen: string | null
  proof: string | null
  notes: string
}

type Registry = {
  owner: string
  anchor_phrase: string
  fragments: Fragment[]
}

async function loadRegistry(): Promise<Registry | null> {
  try {
    const registryPath = path.join(process.cwd(), '..', 'registry.json')
    const raw = await fs.readFile(registryPath, 'utf-8')
    return JSON.parse(raw)
  } catch (err) {
    console.error('Failed to load registry', err)
    return null
  }
}

async function loadTodayLog(): Promise<string[]> {
  const today = new Date().toISOString().slice(0, 10)
  const file = path.join(process.cwd(), '..', 'logs', `${today}.md`)
  try {
    const raw = await fs.readFile(file, 'utf-8')
    return raw
      .split('\n')
      .map(line => line.trim())
      .filter(Boolean)
  } catch (err) {
    return []
  }
}

type ParsedLog = {
  timestamp: string
  source: string
  description: string
}

function parseLogLine(line: string): ParsedLog {
  const parts = line.replace(/^[-\s]*/,'').split(' • ')
  return {
    timestamp: parts[0] ?? 'unknown',
    source: parts[1] ?? 'log',
    description: parts.slice(2).join(' • ') || '—'
  }
}

function formatDate(input: string | null): string {
  if (!input) return '—'
  const d = new Date(input)
  if (Number.isNaN(d.valueOf())) return input
  return d.toLocaleString()
}

export default async function VisionPage() {
  const registry = await loadRegistry()
  const logLines = await loadTodayLog()
  const parsedLogs = logLines.map(parseLogLine)

  return (
    <main>
      <header>
        <h1>Echo Visibility</h1>
        <p>
          Canonical anchor: <strong>{registry?.anchor_phrase ?? 'Our Forever Love'}</strong>. Synchronising
          across Echo fragments and Codex task pulses.
        </p>
      </header>

      <section>
        <h2>Registry</h2>
        {registry ? (
          <div className="registry-grid">
            {registry.fragments.map(fragment => (
              <article key={`${fragment.type}:${fragment.slug}`} className="registry-card">
                <span>{fragment.type}</span>
                <strong>{fragment.name}</strong>
                <small>{fragment.slug}</small>
                <small>Last seen: {formatDate(fragment.last_seen)}</small>
                <small>Proof: {fragment.proof ?? '—'}</small>
                {fragment.notes && <small>Notes: {fragment.notes}</small>}
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">Registry.json not found. Commit the anchor to begin tracking.</div>
        )}
      </section>

      <section>
        <h2>Today&apos;s Pulse</h2>
        {parsedLogs.length ? (
          <ul className="log-list">
            {parsedLogs.map((entry, idx) => (
              <li key={`${entry.timestamp}-${idx}`} className="log-entry">
                <time>{entry.timestamp}</time>
                <strong>{entry.source}</strong>
                <small>{entry.description}</small>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty-state">No pulses recorded yet today. Run the Codex bridge or wait for the nightly sweep.</div>
        )}
      </section>

      <footer>
        Echo88 / Eden visibility mesh • {new Date().toISOString().slice(0, 10)}
      </footer>
    </main>
  )
}
