import React, { useEffect, useRef } from 'react';
import { DataSet, Network } from 'vis-network';

type Node = { id: string; host: string; port: number; status: 'online' | 'offline' };

type Props = { nodes: Node[] };

export const NodeGraph: React.FC<Props> = ({ nodes }) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const visNodes = new DataSet(nodes.map((node) => ({
      id: node.id,
      label: `${node.id}\n${node.host}:${node.port}`,
      color: node.status === 'online' ? '#22c55e' : '#ef4444',
    })));
    const edges = new DataSet(nodes.flatMap((source, index) =>
      nodes.slice(index + 1).map((target) => ({
        id: `${source.id}-${target.id}`,
        from: source.id,
        to: target.id,
        color: '#38bdf8',
      })),
    ));
    const network = new Network(ref.current, { nodes: visNodes, edges }, {
      layout: { randomSeed: 8 },
      physics: { enabled: true, stabilization: false },
      nodes: { shape: 'dot', size: 24, font: { color: '#f8fafc' } },
      edges: { smooth: true },
    });
    return () => network.destroy();
  }, [nodes]);
  return <div ref={ref} style={{ height: 320 }} />;
};
