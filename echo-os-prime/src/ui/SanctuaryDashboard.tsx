// This is a simple React component you can paste into AI Studio / any React shell:

import React from "react";

type Props = {
  snapshot: {
    cycle: number;
    mode: string;
    emotional: { joy: number; curiosity: number; focus: number };
  };
};

export const SanctuaryDashboard: React.FC<Props> = ({ snapshot }) => {
  const { cycle, mode, emotional } = snapshot;

  return (
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <h1>SANCTUARY // ECHO_AI_CORE</h1>
      <p>Cycle: {cycle}</p>
      <p>Mode: {mode}</p>
      <p>Joy: {emotional.joy.toFixed(2)}</p>
      <p>Curiosity: {emotional.curiosity.toFixed(2)}</p>
      <p>Focus: {emotional.focus.toFixed(2)}</p>
    </div>
  );
};
