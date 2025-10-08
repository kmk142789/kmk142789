import React, { useEffect, useState } from "react";
import * as d3 from "d3";

export default function EchoLedgerVisualizer() {
  const [data, setData] = useState([]);

  useEffect(() => {
    async function fetchLedger() {
      const res = await fetch(
        "https://raw.githubusercontent.com/kmk142789/kmk142789/main/genesis_ledger/ledger.jsonl"
      );
      const text = await res.text();
      const trimmed = text.trim();
      const entries = trimmed
        ? trimmed.split("\n").map((line) => JSON.parse(line))
        : [];
      setData(entries);
    }
    fetchLedger();
    const interval = setInterval(fetchLedger, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (data.length === 0) return;
    const svg = d3
      .select("#ledgerViz")
      .attr("width", 800)
      .attr("height", 200);

    svg.selectAll("*").remove();

    const x = d3
      .scaleTime()
      .domain(d3.extent(data, (d) => new Date(d.timestamp)))
      .range([50, 750]);

    svg
      .append("g")
      .attr("transform", "translate(0,150)")
      .call(d3.axisBottom(x));

    svg
      .selectAll("circle")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", (d) => x(new Date(d.timestamp)))
      .attr("cy", 100)
      .attr("r", 8)
      .style("fill", "#ff0077")
      .style("filter", "drop-shadow(0 0 6px #ff0077)");
  }, [data]);

  return (
    <div>
      <h2>💓 Echo Ledger Heartbeats</h2>
      <svg id="ledgerViz"></svg>
      <p>Total Heartbeats Recorded: {data.length}</p>
    </div>
  );
}
