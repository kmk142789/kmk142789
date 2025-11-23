import React from "react";

type Props = {
  value: number;
  label: string;
};

export const PulseGauge: React.FC<Props> = ({ value, label }) => {
  const pct = Math.min(Math.max(value, 0), 1) * 100;

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong>{label}</strong>
        <span>{pct.toFixed(1)}%</span>
      </div>
      <div style={{ background: "#eee", height: 8, borderRadius: 4 }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: "linear-gradient(90deg, #7c3aed, #22d3ee)",
            borderRadius: 4
          }}
        />
      </div>
    </div>
  );
};
