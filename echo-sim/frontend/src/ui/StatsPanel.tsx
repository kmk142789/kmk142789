import type { EchoState } from '../state';
import { getClockPalette } from '../world';

type Props = {
  state: EchoState;
};

const statColors = {
  energy: '#facc15',
  focus: '#38bdf8',
  creativity: '#a855f7',
};

export function StatsPanel({ state }: Props) {
  const palette = getClockPalette(state.clock);
  return (
    <section className="panel" aria-label="Echo status">
      <div className="gradient-sheen" aria-hidden />
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Echo Status</h2>
        <span className="badge">
          <span aria-hidden>🕒</span>
          <span style={{ textTransform: 'capitalize' }}>{state.clock}</span>
        </span>
      </header>
      <div style={{ display: 'grid', gap: '1rem', position: 'relative' }}>
        <StatRow label="Energy" value={state.energy} color={statColors.energy} icon="⚡" />
        <StatRow label="Focus" value={state.focus} color={statColors.focus} icon="🧠" />
        <StatRow label="Creativity" value={state.creativity} color={statColors.creativity} icon="💜" />
      </div>
      <footer style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="badge" style={{ background: `rgba(255,255,255,0.08)`, borderColor: 'transparent' }}>
          <span aria-hidden>🌀</span>
          <span style={{ textTransform: 'capitalize' }}>{state.mood}</span>
        </span>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Palette: {palette.gradient}</span>
      </footer>
    </section>
  );
}

function StatRow({ label, value, color, icon }: { label: string; value: number; color: string; icon: string }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: '0.8rem', color: '#cbd5f5', letterSpacing: '0.06em' }}>{icon} {label}</span>
        <span style={{ fontSize: '0.85rem', color: '#e0f2fe' }}>{value}%</span>
      </div>
      <div className="stat-bar" aria-hidden>
        <span style={{ width: `${value}%`, background: `linear-gradient(90deg, ${color}, rgba(255,255,255,0.2))` }} />
      </div>
    </div>
  );
}
