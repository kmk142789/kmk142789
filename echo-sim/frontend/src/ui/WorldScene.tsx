import { useEffect, useMemo, useRef } from 'react';
import type { EchoState } from '../state';
import { getClockPalette } from '../world';

type Props = {
  state: EchoState;
};

const animationFrames = {
  idle: ['🙂', '😊', '🤔'],
  walk: ['🚶', '🚶‍♀️', '🚶‍♂️'],
  code: ['💻', '🧠', '💡'],
};

export function WorldScene({ state }: Props) {
  const palette = getClockPalette(state.clock);
  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = canvasRef.current;
    if (!node) return;
    node.animate(
      [{ boxShadow: '0 0 30px rgba(56,189,248,0.2)' }, { boxShadow: '0 0 60px rgba(168,85,247,0.4)' }],
      { duration: 6000, iterations: Infinity }
    );
  }, []);

  const echoGlyph = useMemo(() => {
    if (state.focus > 70) return animationFrames.code[state.history.length % 3];
    if (state.energy < 40) return animationFrames.idle[(state.energy % 3 + 3) % 3];
    return animationFrames.walk[state.creativity % 3];
  }, [state.focus, state.energy, state.creativity, state.history.length]);

  return (
    <section className="panel" aria-label="Echo world scene" style={{ position: 'relative', overflow: 'hidden' }}>
      <div className="gradient-sheen" aria-hidden />
      <h2>Studio World</h2>
      <div
        ref={canvasRef}
        style={{
          position: 'relative',
          borderRadius: 18,
          padding: '1.2rem',
          minHeight: 320,
          background: `linear-gradient(160deg, rgba(15,23,42,0.65), rgba(15,23,42,0.25)), linear-gradient(135deg, ${palette.gradient})`,
          display: 'grid',
          placeItems: 'center',
          color: '#0f172a',
        }}
      >
        <svg viewBox="0 0 360 220" style={{ width: '100%', height: '100%' }}>
          <defs>
            <linearGradient id="floor" x1="0%" x2="100%">
              <stop offset="0%" stopColor="rgba(14,116,144,0.5)" />
              <stop offset="100%" stopColor="rgba(8,47,73,0.6)" />
            </linearGradient>
          </defs>
          <rect x="0" y="140" width="360" height="80" fill="url(#floor)" rx="26" />
          <g id="desk" transform="translate(80 120)">
            <rect x="0" y="0" width="140" height="16" rx="8" fill="rgba(148,163,184,0.35)" />
            <rect x="16" y="-36" width="108" height="36" rx="12" fill="rgba(226,232,240,0.8)" />
            <circle cx="32" cy="-16" r="6" fill="#22d3ee" />
          </g>
          <g id="lamp" transform="translate(230 80)">
            <rect x="12" y="42" width="12" height="30" rx="6" fill="rgba(71,85,105,0.8)" />
            <circle cx="18" cy="48" r="18" fill="rgba(250,204,21,0.5)" />
            <circle cx="18" cy="48" r="10" fill="rgba(253,224,71,0.9)" />
          </g>
          <g id="plant" transform="translate(32 120)">
            <rect x="-6" y="12" width="24" height="20" rx="6" fill="rgba(30,64,175,0.65)" />
            <path d="M6 12 C-8 0, 6 -30, 18 -4" fill="rgba(34,197,94,0.5)" />
            <path d="M12 10 C0 -12, 24 -40, 28 -10" fill="rgba(22,163,74,0.5)" />
          </g>
          <g id="door" transform="translate(300 100)">
            <rect x="0" y="-40" width="38" height="110" rx="8" fill="rgba(30,41,59,0.9)" />
            <circle cx="28" cy="16" r="4" fill="rgba(148,163,184,0.8)" />
          </g>
          <text x="180" y="120" fontSize="48" textAnchor="middle">{echoGlyph}</text>
        </svg>
      </div>
    </section>
  );
}
