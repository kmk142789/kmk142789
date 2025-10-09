import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';

export type GraphNode = {
  id: string;
  type: string;
  data?: Record<string, unknown>;
};

export type GraphEdge = {
  source: string;
  target: string;
  rel: string;
  data?: Record<string, unknown>;
};

export type GraphMeta = {
  generated_at: string;
  next_step: string;
};

export type GraphPayload = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  meta: GraphMeta;
};

export type Selection = {
  node: GraphNode;
  edges: GraphEdge[];
  neighbors: GraphNode[];
};

type ForceNode = GraphNode & d3.SimulationNodeDatum;
type ForceLink = GraphEdge & d3.SimulationLinkDatum<ForceNode>;

type Props = {
  onSelect(selection: Selection | null): void;
  onMeta(meta: GraphMeta | null): void;
};

const typeColors: Record<string, string> = {
  repo: '#64b5f6',
  commit: '#ff79c6',
  pr: '#50fa7b',
  module: '#ffa45c',
  symbol: '#f8f87a',
  artifact: '#bd93f9',
};

const dayMs = 24 * 60 * 60 * 1000;

function isRecent(node: GraphNode): boolean {
  if (node.type === 'commit') {
    const timestamp = node.data?.timestamp;
    if (typeof timestamp === 'string') {
      const time = Date.parse(timestamp);
      if (!Number.isNaN(time)) {
        return Date.now() - time <= dayMs;
      }
    }
  }
  return false;
}

export default function Constellation({ onSelect, onMeta }: Props): JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [graph, setGraph] = useState<GraphPayload | null>(null);
  const [positions, setPositions] = useState<ForceNode[]>([]);
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 960,
    height: 720,
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lastStampRef = useRef<string | null>(null);

  const updateSelection = useCallback(
    (nodeId: string | null, data: GraphPayload | null) => {
      if (!nodeId || !data) {
        setSelectedId(null);
        onSelect(null);
        return;
      }
      const node = data.nodes.find((candidate) => candidate.id === nodeId);
      if (!node) {
        setSelectedId(null);
        onSelect(null);
        return;
      }
      const edges = data.edges.filter(
        (edge) => edge.source === nodeId || edge.target === nodeId,
      );
      const neighborIds = new Set(
        edges.flatMap((edge) => [edge.source, edge.target]).filter((id) => id !== nodeId),
      );
      const neighbors = data.nodes.filter((candidate) => neighborIds.has(candidate.id));
      setSelectedId(nodeId);
      onSelect({ node, edges, neighbors });
    },
    [onSelect],
  );

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          setDimensions({
            width: entry.contentRect.width,
            height: entry.contentRect.height,
          });
        }
      }
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const fetchGraph = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`/graph.json?ts=${Date.now()}`, {
        cache: 'no-store',
      });
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      const payload: GraphPayload = await response.json();
      onMeta(payload.meta ?? null);
      if (lastStampRef.current !== payload.meta?.generated_at) {
        lastStampRef.current = payload.meta?.generated_at ?? null;
        setGraph(payload);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load constellation.');
    }
  }, [onMeta]);

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 15_000);
    return () => clearInterval(interval);
  }, [fetchGraph]);

  useEffect(() => {
    if (!graph) {
      return undefined;
    }

    if (selectedId && !graph.nodes.some((node) => node.id === selectedId)) {
      updateSelection(null, graph);
    }

    const nodes: ForceNode[] = graph.nodes.map((node) => ({
      ...node,
      x: dimensions.width / 2 + Math.random() * 40 - 20,
      y: dimensions.height / 2 + Math.random() * 40 - 20,
    }));
    const links: ForceLink[] = graph.edges.map((edge) => ({ ...edge }));

    const simulation = d3
      .forceSimulation(nodes)
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
      .force('link', d3.forceLink<ForceNode, ForceLink>(links).id((node) => node.id).distance(140))
      .force('collision', d3.forceCollide<ForceNode>().radius(() => 38));

    const ticked = () => {
      setPositions(nodes.map((node) => ({ ...node })));
    };

    simulation.on('tick', ticked);
    return () => {
      simulation.on('tick', null);
      simulation.stop();
    };
  }, [graph, dimensions.width, dimensions.height, selectedId, updateSelection]);

  const positionLookup = useMemo(() => {
    const map = new Map<string, ForceNode>();
    for (const node of positions) {
      map.set(node.id, node);
    }
    return map;
  }, [positions]);

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      if (!graph) {
        return;
      }
      updateSelection(nodeId, graph);
    },
    [graph, updateSelection],
  );

  return (
    <div className="constellation" ref={containerRef}>
      {error ? <div className="error-banner">{error}</div> : null}
      <svg width={dimensions.width} height={dimensions.height}>
        <defs>
          <radialGradient id="node-halo" r="65%">
            <stop offset="0%" stopColor="rgba(255, 255, 255, 0.85)" />
            <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
          </radialGradient>
        </defs>
        {graph?.edges.map((edge) => {
          const source = positionLookup.get(edge.source);
          const target = positionLookup.get(edge.target);
          if (!source || !target) {
            return null;
          }
          const isActive = selectedId === edge.source || selectedId === edge.target;
          return (
            <line
              key={`${edge.source}->${edge.target}`}
              x1={source.x ?? 0}
              y1={source.y ?? 0}
              x2={target.x ?? 0}
              y2={target.y ?? 0}
              stroke={isActive ? 'rgba(255, 255, 255, 0.7)' : 'rgba(150, 160, 210, 0.3)'}
              strokeWidth={isActive ? 2.5 : 1.2}
            />
          );
        })}
        {graph?.nodes.map((node) => {
          const position = positionLookup.get(node.id);
          if (!position) {
            return null;
          }
          const color = typeColors[node.type] ?? '#ffffff';
          const isSelected = node.id === selectedId;
          const recent = isRecent(node);
          return (
            <g key={node.id} transform={`translate(${position.x ?? 0}, ${position.y ?? 0})`}>
              {recent ? (
                <circle r={24} fill="url(#node-halo)" opacity={0.5} className="pulse" />
              ) : null}
              <circle
                r={isSelected ? 16 : 12}
                fill={color}
                stroke={isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.3)'}
                strokeWidth={isSelected ? 3 : 1.5}
                onClick={() => handleNodeClick(node.id)}
                style={{ cursor: 'pointer' }}
              />
              <text
                textAnchor="middle"
                y={isSelected ? 30 : 26}
                fill="rgba(232, 236, 255, 0.85)"
                fontSize={12}
              >
                {node.id.split(':')[1] ?? node.id}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
