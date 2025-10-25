import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';

import '../styles.css';

type ContractType = 'math' | 'staking' | 'governance' | 'echo-system';

type PulseForgeFile = {
  path: string;
  additions: number;
  deletions: number;
};

type PulseForgePR = {
  id: string;
  merge_commit: string;
  timestamp: string | null;
  summary: string;
  additions: number;
  deletions: number;
  lines_changed: number;
  contract_type: ContractType;
  files: PulseForgeFile[];
  url: string;
};

type PulseForgeEdge = {
  source: string;
  target: string;
  weight: number;
  files: string[];
};

type PulseForgeHeartbeat = {
  timestamp: string;
  message: string;
  kind: 'evolve' | 'ascend';
};

type PulseForgeDataset = {
  generated_at: string;
  prs: PulseForgePR[];
  edges: PulseForgeEdge[];
  heartbeats: PulseForgeHeartbeat[];
};

type ForgeNode = PulseForgePR & d3.SimulationNodeDatum;
type ForgeLink = PulseForgeEdge & d3.SimulationLinkDatum<ForgeNode>;

type Dimensions = { width: number; height: number };

type Selection = {
  pr: PulseForgePR;
  neighbors: PulseForgePR[];
  sharedFiles: Record<string, string[]>;
};

const TYPE_COLOURS: Record<ContractType, string> = {
  math: '#06b6d4',
  staking: '#10b981',
  governance: '#facc15',
  'echo-system': '#a855f7',
};

const HEARTBEAT_TARGETS: Record<PulseForgeHeartbeat['kind'], ContractType[]> = {
  evolve: ['echo-system', 'math'],
  ascend: ['governance', 'staking'],
};

const HEARTBEAT_INTERVAL = 8000;

export default function PulseForge(): JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [dataset, setDataset] = useState<PulseForgeDataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState<Dimensions>({ width: 960, height: 640 });
  const [positions, setPositions] = useState<ForgeNode[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [heartbeat, setHeartbeat] = useState<PulseForgeHeartbeat | null>(null);
  const [highlighted, setHighlighted] = useState<Set<string>>(new Set());

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          setDimensions({ width: entry.contentRect.width, height: entry.contentRect.height });
        }
      }
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const fetchDataset = async () => {
      try {
        setError(null);
        const response = await fetch(`/pulseforge.json?ts=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload: PulseForgeDataset = await response.json();
        setDataset(payload);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load PulseForge dataset.');
      }
    };
    fetchDataset();
  }, []);

  const radiusScale = useMemo(() => {
    if (!dataset) {
      return (value: number) => 12 + Math.sqrt(value || 1);
    }
    const maxLines = d3.max(dataset.prs, (item) => item.lines_changed) ?? 1;
    const scale = d3.scaleSqrt().domain([0, maxLines || 1]).range([12, 36]);
    return (value: number) => scale(value || 0);
  }, [dataset]);

  useEffect(() => {
    if (!dataset) {
      return undefined;
    }
    const nodes: ForgeNode[] = dataset.prs.map((pr) => ({
      ...pr,
      x: dimensions.width / 2 + (Math.random() - 0.5) * 80,
      y: dimensions.height / 2 + (Math.random() - 0.5) * 80,
    }));
    const links: ForgeLink[] = dataset.edges.map((edge) => ({ ...edge }));

    const simulation = d3
      .forceSimulation(nodes)
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
      .force(
        'link',
        d3
          .forceLink<ForgeNode, ForgeLink>(links)
          .id((node) => node.id)
          .distance((link) => 200 - Math.min(link.weight ?? 1, 6) * 20)
          .strength((link) => 0.3 + Math.min(link.weight ?? 1, 5) * 0.08),
      )
      .force('collision', d3.forceCollide<ForgeNode>().radius((node) => radiusScale(node.lines_changed) + 8));

    simulation.on('tick', () => {
      setPositions(nodes.map((node) => ({ ...node })));
    });

    return () => {
      simulation.stop();
    };
  }, [dataset, dimensions, radiusScale]);

  useEffect(() => {
    if (!dataset || !dataset.heartbeats.length) {
      setHeartbeat(null);
      return undefined;
    }

    let index = 0;
    const cycle = () => {
      setHeartbeat(dataset.heartbeats[index]);
      index = (index + 1) % dataset.heartbeats.length;
    };
    cycle();
    const timer = window.setInterval(cycle, HEARTBEAT_INTERVAL);
    return () => window.clearInterval(timer);
  }, [dataset]);

  useEffect(() => {
    if (!heartbeat || !dataset) {
      setHighlighted(new Set());
      return;
    }
    const targets = new Set(HEARTBEAT_TARGETS[heartbeat.kind]);
    const active = new Set(dataset.prs.filter((pr) => targets.has(pr.contract_type)).map((pr) => pr.id));
    setHighlighted(active);
  }, [heartbeat, dataset]);

  const positionLookup = useMemo(() => {
    const map = new Map<string, ForgeNode>();
    positions.forEach((node) => {
      map.set(node.id, node);
    });
    return map;
  }, [positions]);

  const currentSelection = useMemo(() => {
    if (!dataset || !selectedId) {
      setSelection(null);
      return null;
    }
    const node = dataset.prs.find((pr) => pr.id === selectedId);
    if (!node) {
      setSelection(null);
      return null;
    }
    const neighborMap: Record<string, string[]> = {};
    const neighbors = new Map<string, PulseForgePR>();
    dataset.edges.forEach((edge) => {
      if (edge.source === node.id || edge.target === node.id) {
        const otherId = edge.source === node.id ? edge.target : edge.source;
        const neighbor = dataset.prs.find((candidate) => candidate.id === otherId);
        if (neighbor) {
          neighbors.set(neighbor.id, neighbor);
          neighborMap[neighbor.id] = edge.files;
        }
      }
    });
    const details: Selection = {
      pr: node,
      neighbors: Array.from(neighbors.values()),
      sharedFiles: neighborMap,
    };
    setSelection(details);
    return details;
  }, [dataset, selectedId]);

  const heartbeatLabel = useMemo(() => {
    if (!heartbeat) {
      return 'Awaiting heartbeat';
    }
    const time = new Date(heartbeat.timestamp).toLocaleString();
    return `${heartbeat.kind === 'ascend' ? 'Ascend' : 'Evolve'} · ${time}`;
  }, [heartbeat]);

  return (
    <div className="pulseforge" ref={containerRef}>
      {error ? <div className="error-banner">{error}</div> : null}
      <svg className="pulseforge-canvas" width={dimensions.width} height={dimensions.height}>
        <defs>
          <radialGradient id="pulseforge-glow" r="70%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.9)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0)" />
          </radialGradient>
        </defs>
        {dataset?.edges.map((edge) => {
          const source = positionLookup.get(edge.source);
          const target = positionLookup.get(edge.target);
          if (!source || !target) {
            return null;
          }
          const active = highlighted.has(edge.source) || highlighted.has(edge.target);
          const weight = edge.weight ?? 1;
          return (
            <line
              key={`${edge.source}->${edge.target}`}
              x1={source.x ?? 0}
              y1={source.y ?? 0}
              x2={target.x ?? 0}
              y2={target.y ?? 0}
              stroke={active ? 'rgba(255,255,255,0.65)' : 'rgba(148, 163, 184, 0.35)'}
              strokeWidth={1 + Math.min(weight, 6) * 0.6}
              className={active ? 'pulseforge-link pulseforge-link--active' : 'pulseforge-link'}
            />
          );
        })}
        {dataset?.prs.map((node) => {
          const position = positionLookup.get(node.id);
          if (!position) {
            return null;
          }
          const radius = radiusScale(node.lines_changed);
          const isSelected = node.id === selectedId;
          const isHighlighted = highlighted.has(node.id);
          return (
            <g
              key={node.id}
              transform={`translate(${position.x ?? 0}, ${position.y ?? 0})`}
              className={isHighlighted ? 'pulseforge-node pulseforge-node--lit' : 'pulseforge-node'}
              onClick={() => setSelectedId(node.id)}
            >
              <circle r={radius + 10} fill="url(#pulseforge-glow)" opacity={isHighlighted ? 0.85 : 0.4} />
              <circle
                r={radius}
                fill={TYPE_COLOURS[node.contract_type]}
                stroke={isSelected ? '#ffffff' : 'rgba(15, 23, 42, 0.6)'}
                strokeWidth={isSelected ? 4 : 2}
              />
              <text textAnchor="middle" y={radius + 16} className="pulseforge-label">
                #{node.id}
              </text>
            </g>
          );
        })}
      </svg>
      <div className={`pulseforge-heartbeat ${heartbeat ? 'pulseforge-heartbeat--active' : ''} pulseforge-heartbeat--${heartbeat?.kind ?? 'idle'}`}>
        <span>{heartbeatLabel}</span>
        <span className="pulseforge-heartbeat__message">{heartbeat?.message ?? '—'}</span>
      </div>
      <div className="pulseforge-panel">
        {selection ? (
          <>
            <h2>Pulse #{selection.pr.id}</h2>
            <p className="muted">{selection.pr.timestamp ? new Date(selection.pr.timestamp).toLocaleString() : 'Unknown time'}</p>
            <p>{selection.pr.summary}</p>
            <dl className="pulseforge-stats">
              <div>
                <dt>Lines +</dt>
                <dd>{selection.pr.additions.toLocaleString()}</dd>
              </div>
              <div>
                <dt>Lines −</dt>
                <dd>{selection.pr.deletions.toLocaleString()}</dd>
              </div>
              <div>
                <dt>Contract</dt>
                <dd className={`pulseforge-contract pulseforge-contract--${selection.pr.contract_type}`}>
                  {selection.pr.contract_type}
                </dd>
              </div>
            </dl>
            <h3>Linked Files</h3>
            <ul className="pulseforge-files">
              {selection.pr.files.slice(0, 8).map((file) => (
                <li key={file.path}>
                  <a href={`https://github.com/kmk142789/kmk142789/blob/main/${file.path}`} target="_blank" rel="noreferrer">
                    {file.path}
                  </a>
                  <span className="muted">
                    +{file.additions.toLocaleString()} / −{file.deletions.toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
            {selection.neighbors.length ? (
              <div className="pulseforge-neighbours">
                <h3>Connected Pulses</h3>
                <ul>
                  {selection.neighbors.map((neighbor) => (
                    <li key={neighbor.id}>
                      <button type="button" onClick={() => setSelectedId(neighbor.id)}>
                        #{neighbor.id} · {neighbor.summary}
                      </button>
                      {selection.sharedFiles[neighbor.id]?.length ? (
                        <p className="muted">
                          Shared files: {selection.sharedFiles[neighbor.id].slice(0, 3).join(', ')}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <p className="muted">
              <a href={selection.pr.url} target="_blank" rel="noreferrer">
                View pull request ↗
              </a>
            </p>
          </>
        ) : (
          <div className="pulseforge-placeholder">
            <h2>Echo Codex PulseForge</h2>
            <p>Select a glyph to reveal its merged story.</p>
            <p className="muted">Node size reflects lines changed. Colour denotes contract class.</p>
          </div>
        )}
      </div>
    </div>
  );
}
