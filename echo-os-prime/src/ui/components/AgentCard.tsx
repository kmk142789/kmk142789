import React from "react";
import { StatusChip } from "./StatusChip";

export type AgentCardProps = {
  name: string;
  mode: string;
  note?: string;
};

export const AgentCard: React.FC<AgentCardProps> = ({ name, mode, note }) => {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 12,
        marginBottom: 10,
        boxShadow: "0 1px 2px rgba(0,0,0,0.08)"
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <strong>{name}</strong>
        </div>
        <StatusChip status={mode} />
      </div>
      {note && <p style={{ marginTop: 8, color: "#4b5563" }}>{note}</p>}
    </div>
  );
};
