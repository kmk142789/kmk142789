import React from "https://esm.sh/react@18.2.0";
import ReactDOM from "https://esm.sh/react-dom@18.2.0/client";
import * as d3 from "https://esm.sh/d3@7.8.5";

const REFRESH_INTERVAL = 60_000;
const DATA_URL = "../../federated_attestation_index.json";
const h = React.createElement;

function useAttestationData() {
  const [payload, setPayload] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [refreshing, setRefreshing] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setRefreshing(true);
      try {
        const cacheBust = Date.now();
        const response = await fetch(`${DATA_URL}?${cacheBust}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        if (!cancelled) {
          setPayload(json);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setRefreshing(false);
        }
      }
    }

    fetchData();
    const timer = setInterval(fetchData, REFRESH_INTERVAL);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return { payload, error, refreshing };
}

function buildGraphData(payload) {
  if (!payload) {
    return { nodes: [], links: [] };
  }
  const nodes = [];
  const links = [];
  const seenPuzzles = new Set();

  for (const entry of payload.nodes || []) {
    const puzzleKey = `p-${entry.puzzle}`;
    if (!seenPuzzles.has(puzzleKey)) {
      seenPuzzles.add(puzzleKey);
      nodes.push({
        id: puzzleKey,
        label: `Puzzle ${entry.puzzle}`,
        type: "puzzle",
        entry,
      });
    }

    const attKey = `a-${entry.puzzle}-${entry.cycle}`;
    nodes.push({
      id: attKey,
      label: `Cycle ${entry.cycle}`,
      type: entry.status === "attested" ? "attestation" : "warning",
      entry,
    });
    links.push({ source: puzzleKey, target: attKey });

    if (entry.analysis && entry.analysis.type === "invalid") {
      const anomalyKey = `anom-${entry.puzzle}-${entry.cycle}`;
      nodes.push({
        id: anomalyKey,
        label: "PKScript anomaly",
        type: "anomaly",
        entry,
      });
      links.push({ source: attKey, target: anomalyKey });
    }
  }

  return { nodes, links };
}

function ForceGraph({ data }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    if (!data.nodes.length) return;

    const { width, height } = ref.current.getBoundingClientRect();
    const viewWidth = width || 640;
    const viewHeight = height || 480;
    svg.attr("viewBox", `0 0 ${viewWidth} ${viewHeight}`);

    const simulation = d3
      .forceSimulation(data.nodes)
      .force(
        "link",
        d3
          .forceLink(data.links)
          .id((d) => d.id)
          .distance((link) => (link.target.type === "anomaly" ? 140 : 95))
          .strength(0.35)
      )
      .force("charge", d3.forceManyBody().strength(-240))
      .force("center", d3.forceCenter(viewWidth / 2, viewHeight / 2))
      .force("collision", d3.forceCollide().radius(55));

    const link = svg
      .append("g")
      .attr("stroke", "rgba(144, 128, 255, 0.32)")
      .attr("stroke-width", 1.5)
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke-dasharray", (d) => (d.target.type === "anomaly" ? "4 4" : null));

    const colorMap = {
      puzzle: "#5a0fc8",
      attestation: "#5de4c7",
      warning: "#f7b955",
      anomaly: "#f45c7a",
    };

    const node = svg
      .append("g")
      .selectAll("g")
      .data(data.nodes)
      .enter()
      .append("g")
      .attr("role", "listitem")
      .attr("aria-label", (d) => d.label);

    node
      .append("circle")
      .attr("r", (d) => (d.type === "puzzle" ? 22 : d.type === "anomaly" ? 14 : 18))
      .attr("fill", (d) => colorMap[d.type] || "#f4f3ff")
      .attr("fill-opacity", 0.85)
      .attr("stroke", "rgba(10, 10, 18, 0.7)")
      .attr("stroke-width", 2.5);

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 5)
      .attr("font-size", 10)
      .attr("fill", "#0c0c12")
      .text((d) => (d.type === "puzzle" ? d.label.replace("Puzzle", "P") : d.label));

    node.call(
      d3
        .drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
    );

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [data]);

  return h("svg", { ref, className: "constellation" });
}

function StatPills({ payload }) {
  if (!payload) return null;
  const total = payload.nodes?.length || 0;
  const anomalies = (payload.nodes || []).filter(
    (entry) => entry.analysis?.type === "invalid"
  ).length;
  const refreshed = new Date(payload.generated_at || Date.now());
  const latestCycle = Math.max(...(payload.nodes || []).map((entry) => entry.cycle || 0), 0);

  return h(
    "div",
    { className: "stats" },
    h("span", { className: "stat-pill" }, `Total attestations: ${total}`),
    h("span", { className: "stat-pill" }, `Latest cycle: ${latestCycle}`),
    h(
      "span",
      { className: "stat-pill" },
      anomalies ? `${anomalies} anomaly flag${anomalies === 1 ? "" : "s"}` : "No anomalies"
    ),
    h("span", { className: "stat-pill" }, `Refreshed ${refreshed.toUTCString()}`)
  );
}

function AttestationCard({ entry }) {
  const statusGood = entry.status === "attested";
  const links = entry.links || {};
  return h(
    "article",
    { className: "attestation" },
    h("h3", null, `Puzzle ${entry.puzzle} · Cycle ${entry.cycle}`),
    h(
      "small",
      null,
      `Address ${entry.address} · Hash ${entry.metadata?.hash_sha256 ?? "n/a"}`
    ),
    h(
      "div",
      { className: statusGood ? "status-pill" : "status-pill warn" },
      statusGood ? "✅ Attested" : "⚠️ Attention needed"
    ),
    entry.narrative
      ? h("p", { style: { marginTop: "0.75rem", color: "var(--muted)" } }, entry.narrative)
      : null,
    h(
      "p",
      { style: { marginTop: "0.75rem", fontSize: "0.85rem" } },
      links.commit
        ? h(
            "a",
            { href: `../../${links.commit}`, target: "_blank", rel: "noopener" },
            "Latest commit"
          )
        : null,
      links.history
        ? h(
            React.Fragment,
            null,
            links.commit ? " · " : null,
            h(
              "a",
              { href: `../../${links.history}`, target: "_blank", rel: "noopener" },
              "History"
            )
          )
        : null,
      links.file
        ? h(
            React.Fragment,
            null,
            links.commit || links.history ? " · " : null,
            h("a", { href: `../../${links.file}`, target: "_blank" }, "Source JSON")
          )
        : null
    )
  );
}

function Dashboard() {
  const { payload, error, refreshing } = useAttestationData();
  const graphData = React.useMemo(() => buildGraphData(payload), [payload]);

  return h(
    React.Fragment,
    null,
    h(
      "header",
      null,
      h("h1", null, "Federated Attestation Constellation"),
      h(
        "p",
        null,
        "Live GitHub Pages dashboard drawing from ",
        h("code", null, "federated_attestation_index.json"),
        ". Every refresh folds new attestations, PKScript analyses, and anomaly flags into a force-directed graph."
      )
    ),
    h(
      "main",
      null,
      h(
        "section",
        { className: "card graph-card" },
        h(StatPills, { payload }),
        h("div", { className: "graph-wrapper" }, h(ForceGraph, { data: graphData })),
        h(
          "div",
          { className: "refresh-indicator" },
          refreshing
            ? "Refreshing constellation…"
            : payload
            ? `Last synced ${new Date(payload.generated_at || Date.now()).toUTCString()}`
            : "Awaiting first sync"
        ),
        error
          ? h(
              "div",
              { className: "refresh-indicator", style: { color: "var(--danger)" } },
              `Data fetch failed: ${error}`
            )
          : null
      ),
      h(
        "aside",
        { className: "card" },
        h("h2", null, "Attestation Stream"),
        h(
          "div",
          { className: "list", role: "feed" },
          payload
            ? (payload.nodes || []).map((entry) =>
                h(AttestationCard, { entry, key: `${entry.puzzle}-${entry.cycle}` })
              )
            : h("p", { className: "refresh-indicator" }, "Loading constellation…")
        )
      )
    ),
    h(
      "footer",
      null,
      "Auto-refreshed every 60s · Powered by ",
      h("code", null, "scripts/build_federated_attestation_index.py"),
      " · Echo Continuum live."
    )
  );
}

const root = ReactDOM.createRoot(document.getElementById("app-root"));
root.render(h(Dashboard));
