const { useState, useMemo, useEffect, useCallback, useRef } = React;

const DATA_URL = "../build/index/federated_colossus_index.json";
const REFRESH_INTERVAL = 60000;

function useAutoRefreshingData(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const response = await fetch(`${url}?t=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const json = await response.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err);
    }
  }, [url]);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_INTERVAL);
    return () => clearInterval(timer);
  }, [load]);

  return { data, error, reload: load };
}

function buildGraphModel(data, filteredEntries) {
  const constellations = data?.constellations ?? [];
  const notices = data?.safety?.notices ?? [];
  const flagged = notices.filter((notice) => notice.flagged);

  const entryKeys = new Set(
    filteredEntries.map((entry) => `${entry.puzzle_id}:${(entry.address || "").toLowerCase()}`)
  );

  const activeConstellations = constellations.filter((node) => {
    if (!entryKeys.size) {
      return true;
    }
    const key = `${node.puzzle}:${(node.address || "").toLowerCase()}`;
    return entryKeys.has(key);
  }).slice(0, 60);

  const nodes = [];
  const links = [];
  const nodeById = new Map();

  const addNode = (id, type, label, meta = {}) => {
    if (nodeById.has(id)) {
      return nodeById.get(id);
    }
    const node = { id, type, label, meta };
    nodeById.set(id, node);
    nodes.push(node);
    return node;
  };

  activeConstellations.forEach((node) => {
    const puzzleNode = addNode(
      `puzzle-${node.puzzle}`,
      "puzzle",
      `Puzzle #${node.puzzle}`,
      { cycle: node.cycle }
    );
    const attestationNode = addNode(
      `att-${node.puzzle}-${node.address}`,
      "attestation",
      `${node.status_icon || ""} ${node.address}`,
      node
    );
    links.push({ source: puzzleNode.id, target: attestationNode.id, strength: 1 });
  });

  flagged.forEach((notice) => {
    const label = notice.title || notice.id || "Continuum Breach";
    const anomalyNode = addNode(
      `anomaly-${label}`,
      "anomaly",
      `⚠️ ${label}`,
      notice
    );
    activeConstellations.forEach((entry) => {
      links.push({ source: anomalyNode.id, target: `att-${entry.puzzle}-${entry.address}`, strength: 0.3 });
    });
  });

  return { nodes, links };
}

function ForceGraph({ nodes, links }) {
  const svgRef = useRef(null);

  useEffect(() => {
    const svgElement = svgRef.current;
    if (!svgElement || !nodes.length) {
      return;
    }

    const width = svgElement.clientWidth || 800;
    const height = svgElement.clientHeight || 420;

    const simNodes = nodes.map((node) => ({ ...node }));
    const simLinks = links.map((link) => ({ ...link }));

    const svg = d3.select(svgElement);
    svg.selectAll("*").remove();

    const linkGroup = svg
      .append("g")
      .attr("stroke", "#d1d5db")
      .attr("stroke-width", 1.2)
      .selectAll("line")
      .data(simLinks)
      .enter()
      .append("line");

    const colorMap = {
      puzzle: "#2563eb",
      attestation: "#0ea5e9",
      anomaly: "#f97316",
    };

    const nodeGroup = svg
      .append("g")
      .selectAll("g")
      .data(simNodes)
      .enter()
      .append("g")
      .attr("class", "fg-node");

    nodeGroup
      .append("circle")
      .attr("r", (node) => (node.type === "attestation" ? 10 : node.type === "anomaly" ? 12 : 8))
      .attr("fill", (node) => colorMap[node.type] || "#6366f1")
      .attr("stroke", "#0f172a")
      .attr("stroke-width", 1.2);

    nodeGroup
      .append("title")
      .text((node) => node.label);

    nodeGroup
      .append("text")
      .attr("text-anchor", "middle")
      .attr("y", 18)
      .attr("class", "fg-label")
      .text((node) => node.label);

    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3
          .forceLink(simLinks)
          .id((node) => node.id)
          .distance((link) => (link.strength === 0.3 ? 160 : 90))
          .strength((link) => link.strength || 0.6)
      )
      .force("charge", d3.forceManyBody().strength(-240))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(28));

    simulation.on("tick", () => {
      linkGroup
        .attr("x1", (link) => link.source.x)
        .attr("y1", (link) => link.source.y)
        .attr("x2", (link) => link.target.x)
        .attr("y2", (link) => link.target.y);

      nodeGroup.attr("transform", (node) => `translate(${node.x}, ${node.y})`);
    });

    return () => simulation.stop();
  }, [nodes, links]);

  return <svg ref={svgRef} className="force-graph" viewBox="0 0 960 420"></svg>;
}

function SummaryCard({ label, value }) {
  return (
    <div className="summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function App() {
  const { data, error, reload } = useAutoRefreshingData(DATA_URL);
  const [filters, setFilters] = useState({ cycle: "", puzzle: "", address: "" });

  const entries = data?.entries ?? [];
  const filteredEntries = useMemo(() => {
    return entries
      .filter((entry) => {
        if (filters.cycle && Number(entry.cycle) !== Number(filters.cycle)) return false;
        if (filters.puzzle && Number(entry.puzzle_id) !== Number(filters.puzzle)) return false;
        if (filters.address && !String(entry.address || "").toLowerCase().startsWith(filters.address.toLowerCase())) return false;
        return true;
      })
      .slice(0, 500);
  }, [entries, filters]);

  const graphModel = useMemo(() => buildGraphModel(data, filteredEntries), [data, filteredEntries]);

  const refreshedLabel = data?.refreshed_at ? `Refreshed ${data.refreshed_at}` : "Awaiting data";
  const totals = data?.totals || { entries: 0, cycles: 0, puzzles: 0 };

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>Federated Colossus — Live Index</h1>
          <p className="muted">{refreshedLabel} · auto-refresh {REFRESH_INTERVAL / 1000}s cadence</p>
        </div>
        <div className="summary-grid">
          <SummaryCard label="Entries" value={totals.entries} />
          <SummaryCard label="Cycles" value={totals.cycles} />
          <SummaryCard label="Puzzles" value={totals.puzzles} />
        </div>
      </header>

      <section className="card">
        <h2>Proof Filters</h2>
        <div className="filters">
          <label>
            Cycle
            <input
              value={filters.cycle}
              onChange={(event) => setFilters((state) => ({ ...state, cycle: event.target.value }))}
              placeholder="e.g. 11"
            />
          </label>
          <label>
            Puzzle
            <input
              value={filters.puzzle}
              onChange={(event) => setFilters((state) => ({ ...state, puzzle: event.target.value }))}
              placeholder="e.g. 213"
            />
          </label>
          <label>
            Address
            <input
              value={filters.address}
              onChange={(event) => setFilters((state) => ({ ...state, address: event.target.value }))}
              placeholder="prefix ok"
            />
          </label>
          <div className="filter-actions">
            <button onClick={() => reload()}>Refresh</button>
            <button onClick={() => setFilters({ cycle: "", puzzle: "", address: "" })}>Clear</button>
          </div>
        </div>
        <p className="muted">
          Data source: <code>{DATA_URL}</code>
        </p>
        {error && <p className="error">Failed to load index — {error.message}</p>}
      </section>

      <section className="card">
        <h2>Constellation Graph</h2>
        <p className="muted">Puzzles, attestations, and flagged anomalies orbit in a force-directed mesh.</p>
        <ForceGraph nodes={graphModel.nodes} links={graphModel.links} />
      </section>

      <section className="card">
        <h2>Attestation Entries ({filteredEntries.length})</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Cycle</th>
                <th>Puzzle</th>
                <th>Address</th>
                <th>Digest</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((entry) => (
                <tr key={`${entry.cycle}-${entry.puzzle_id}-${entry.address}`}>
                  <td>{entry.cycle}</td>
                  <td>{entry.puzzle_id}</td>
                  <td className="mono">{entry.address}</td>
                  <td className="mono">{entry.digest}</td>
                  <td className="muted">{entry.source}</td>
                </tr>
              ))}
              {!filteredEntries.length && (
                <tr>
                  <td colSpan={5} className="muted">
                    No entries match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
