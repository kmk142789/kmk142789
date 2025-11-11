import React from 'react';

type Metric = { name: string; value: number; timestamp: number };
type Drive = { id: string; capacity: number; used: number };

type Props = {
  metrics: Metric[];
  drives: Drive[];
};

const formatValue = (value: number) => value.toFixed(2);

export const MetricsPanel: React.FC<Props> = ({ metrics, drives }) => {
  return (
    <div>
      <h2>Realtime Metrics</h2>
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div key={`${metric.name}-${metric.timestamp}`} className="metric-card">
            <h3>{metric.name}</h3>
            <p>{formatValue(metric.value)}</p>
          </div>
        ))}
      </div>
      <h2>Storage Drives</h2>
      <div className="metrics-grid">
        {drives.map((drive) => (
          <div key={drive.id} className="metric-card">
            <h3>{drive.id}</h3>
            <p>
              {drive.used} / {drive.capacity} GiB
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
