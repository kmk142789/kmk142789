import React from "react";

const colors: Record<string, string> = {
  NEUTRAL: "#6b7280",
  FOCUSED: "#2563eb",
  SURGE: "#f59e0b"
};

type Props = {
  status: string;
};

export const StatusChip: React.FC<Props> = ({ status }) => {
  const color = colors[status] ?? "#10b981";

  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 8px",
        borderRadius: 999,
        background: color,
        color: "white",
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: 0.5
      }}
    >
      {status}
    </span>
  );
};
