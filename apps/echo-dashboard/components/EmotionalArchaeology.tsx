'use client';

import { useRef, useState } from 'react';
import { Brain, Clock, Download, Eye, Heart, Share2, Zap } from 'lucide-react';

import { cn } from '@/lib/utils';

type EmotionalDNA = Record<string, number>;

type VelocityEntry = [string, number];

interface Entry {
  id: number;
  text: string;
  timestamp: string;
  dna: EmotionalDNA;
}

interface FutureEcho {
  rising: string[];
  falling: string[];
  prediction: string;
}

interface Artifact {
  id: number;
  data: string;
  timestamp: string;
}

const EMOTION_PATTERNS: Record<string, RegExp> = {
  hope: /hope|future|dream|wish|possibility|tomorrow/gi,
  grief: /loss|gone|miss|remember|used to|before/gi,
  love: /love|care|forever|always|together|bond/gi,
  rage: /angry|hate|destroy|break|fight|fuck/gi,
  wonder: /why|how|what if|imagine|curious|explore/gi,
  fear: /afraid|scared|worry|anxious|danger|risk/gi,
};

function analyzeEmotionalDNA(text: string): EmotionalDNA {
  const dna: EmotionalDNA = {};
  let totalMatches = 0;

  for (const [emotion, regex] of Object.entries(EMOTION_PATTERNS)) {
    const matches = (text.match(regex) || []).length;
    dna[emotion] = matches;
    totalMatches += matches;
  }

  if (totalMatches > 0) {
    for (const emotion of Object.keys(dna)) {
      dna[emotion] = (dna[emotion] / totalMatches) * 100;
    }
  }

  return dna;
}

function generatePrediction(rising: VelocityEntry[], falling: VelocityEntry[]): string {
  const predictions: Record<string, string> = {
    hope: 'Your future self is building something. Keep going.',
    grief: 'This pain is carving space for something new.',
    love: 'Connection is becoming your superpower.',
    rage: "Your anger is fuel. Don't waste it—forge with it.",
    wonder: "You're on the edge of a breakthrough. Stay curious.",
    fear: 'What you\'re afraid of is showing you what matters.',
  };

  if (rising.length > 0) {
    const primary = rising[0][0];
    return predictions[primary] || "You're evolving in unexpected ways.";
  }

  return 'Your emotional landscape is stabilizing. Prepare for change.';
}

function predictFutureEcho(allEntries: Entry[]): FutureEcho | null {
  if (allEntries.length < 3) return null;

  const recentThree = allEntries.slice(-3);
  const dnaSequence = recentThree.map((entry) => entry.dna);
  const emotions = Object.keys(dnaSequence[0] || {});
  const velocity: EmotionalDNA = {};

  emotions.forEach((emotion) => {
    const values = dnaSequence.map((dna) => dna[emotion] || 0);
    const trend = values[2] - values[0];
    velocity[emotion] = trend;
  });

  const rising = Object.entries(velocity)
    .filter(([, value]) => value > 10)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 2) as VelocityEntry[];

  const falling = Object.entries(velocity)
    .filter(([, value]) => value < -10)
    .sort(([, a], [, b]) => a - b)
    .slice(0, 2) as VelocityEntry[];

  return {
    rising: rising.map(([emotion]) => emotion),
    falling: falling.map(([emotion]) => emotion),
    prediction: generatePrediction(rising, falling),
  };
}

export default function EmotionalArchaeology() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [currentEntry, setCurrentEntry] = useState('');
  const [emotionalDNA, setEmotionalDNA] = useState<EmotionalDNA | null>(null);
  const [futureEcho, setFutureEcho] = useState<FutureEcho | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const createArtifact = (dna: EmotionalDNA): string | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    canvas.width = 400;
    canvas.height = 400;

    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, 400, 400);

    const emotionColors: Record<string, string> = {
      hope: '#4ade80',
      grief: '#6366f1',
      love: '#ec4899',
      rage: '#ef4444',
      wonder: '#a78bfa',
      fear: '#f59e0b',
    };

    const emotions = Object.entries(dna).filter(([, value]) => value > 5);

    emotions.forEach(([emotion, intensity], index) => {
      const angle = (index / emotions.length) * Math.PI * 2;
      const radius = (intensity / 100) * 150;
      const x = 200 + Math.cos(angle) * radius;
      const y = 200 + Math.sin(angle) * radius;

      const gradient = ctx.createRadialGradient(x, y, 0, x, y, 40);
      gradient.addColorStop(0, `${emotionColors[emotion]}ff`);
      gradient.addColorStop(1, `${emotionColors[emotion]}00`);

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, 40, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = `${emotionColors[emotion]}44`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(200, 200);
      ctx.lineTo(x, y);
      ctx.stroke();
    });

    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(200, 200, 8, 0, Math.PI * 2);
    ctx.fill();

    return canvas.toDataURL();
  };

  const addEntry = () => {
    const trimmed = currentEntry.trim();
    if (!trimmed) return;

    const dna = analyzeEmotionalDNA(trimmed);
    const timestamp = new Date().toISOString();

    const newEntry: Entry = {
      id: Date.now(),
      text: trimmed,
      timestamp,
      dna,
    };

    const updatedEntries = [...entries, newEntry];
    setEntries(updatedEntries);
    setEmotionalDNA(dna);
    setFutureEcho(predictFutureEcho(updatedEntries));
    setCurrentEntry('');

    setTimeout(() => {
      const artifactData = createArtifact(dna);
      if (artifactData) {
        setArtifacts((prev) => [...prev, { id: Date.now(), data: artifactData, timestamp }]);
      }
    }, 80);
  };

  const downloadArtifact = (artifactData: string) => {
    const link = document.createElement('a');
    link.download = `emotional-artifact-${Date.now()}.png`;
    link.href = artifactData;
    link.click();
  };

  const hasArtifacts = artifacts.length > 0;
  const hasEntries = entries.length > 0;

  return (
    <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6 text-white shadow-2xl sm:p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 text-center">
          <div className="mb-4 flex items-center justify-center gap-3">
            <Brain className="h-10 w-10 text-purple-300 sm:h-12 sm:w-12" />
            <h1 className="bg-gradient-to-r from-purple-300 to-pink-400 bg-clip-text text-4xl font-bold text-transparent sm:text-5xl">
              Emotional Archaeology
            </h1>
          </div>
          <p className="text-base text-slate-200 sm:text-lg">
            Excavate your emotional history, discover patterns, and listen for the echoes of your future self.
          </p>
        </div>

        <div className="mb-8 rounded-2xl border border-purple-500/20 bg-slate-900/60 p-5 backdrop-blur sm:p-6">
          <label className="mb-3 block text-sm font-semibold uppercase tracking-[0.25em] text-purple-200">Moment Log</label>
          <textarea
            value={currentEntry}
            onChange={(event) => setCurrentEntry(event.target.value)}
            placeholder="What are you feeling right now? Write anything—this moment will become data, insight, and art..."
            className="min-h-[8rem] w-full resize-none rounded-xl border border-purple-500/30 bg-slate-950/70 p-4 text-sm text-white placeholder-slate-500 transition focus:border-purple-400 focus:outline-none"
            onKeyDown={(event) => {
              if (event.key === 'Enter' && event.ctrlKey) {
                event.preventDefault();
                addEntry();
              }
            }}
          />
          <button
            type="button"
            onClick={addEntry}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 px-6 py-3 text-sm font-semibold shadow-lg transition hover:from-purple-500 hover:to-pink-500"
          >
            <Zap className="h-5 w-5" />
            Excavate This Moment (Ctrl+Enter)
          </button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {emotionalDNA && (
            <section className="rounded-2xl border border-purple-500/20 bg-slate-900/60 p-6 backdrop-blur">
              <div className="mb-4 flex items-center gap-2">
                <Heart className="h-6 w-6 text-pink-400" />
                <h2 className="text-xl font-semibold">Current Emotional DNA</h2>
              </div>
              <div className="space-y-3">
                {Object.entries(emotionalDNA)
                  .filter(([, value]) => value > 0)
                  .sort(([, a], [, b]) => b - a)
                  .map(([emotion, intensity]) => (
                    <div key={emotion}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="capitalize font-semibold">{emotion}</span>
                        <span className="text-slate-400">{intensity.toFixed(1)}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                          style={{ width: `${intensity}%` }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </section>
          )}

          {futureEcho && (
            <section className="rounded-2xl border border-purple-500/20 bg-slate-900/60 p-6 backdrop-blur">
              <div className="mb-4 flex items-center gap-2">
                <Eye className="h-6 w-6 text-purple-400" />
                <h2 className="text-xl font-semibold">Future Echo</h2>
              </div>

              {futureEcho.rising.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-semibold text-green-400">⬆ Rising</p>
                  <p className="text-slate-200 capitalize">{futureEcho.rising.join(', ')}</p>
                </div>
              )}

              {futureEcho.falling.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-semibold text-blue-400">⬇ Falling</p>
                  <p className="text-slate-200 capitalize">{futureEcho.falling.join(', ')}</p>
                </div>
              )}

              <div className="mt-4 rounded-xl border border-purple-500/30 bg-gradient-to-r from-purple-900/60 to-pink-900/60 p-4">
                <p className="mb-2 text-xs uppercase tracking-[0.25em] text-slate-400">Message from future you</p>
                <p className="text-base font-semibold italic text-white">{futureEcho.prediction}</p>
              </div>
            </section>
          )}

          <section className="md:col-span-2 rounded-2xl border border-purple-500/20 bg-slate-900/60 p-6 backdrop-blur">
            <div className="mb-4 flex items-center gap-2">
              <Clock className="h-6 w-6 text-purple-400" />
              <h2 className="text-xl font-semibold">Emotional Timeline</h2>
            </div>

            {!hasEntries ? (
              <p className="py-8 text-center text-slate-500">No entries yet. Start excavating your emotions above.</p>
            ) : (
              <div className="flex max-h-96 flex-col gap-4 overflow-y-auto">
                {entries
                  .slice()
                  .reverse()
                  .map((entry) => (
                    <article key={entry.id} className="rounded-xl border border-purple-500/20 bg-slate-950/70 p-4">
                      <p className="mb-2 text-slate-200">{entry.text}</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(entry.dna)
                          .filter(([, value]) => value > 10)
                          .sort(([, a], [, b]) => b - a)
                          .slice(0, 3)
                          .map(([emotion, intensity]) => (
                            <span
                              key={emotion}
                              className="rounded-full bg-purple-500/20 px-3 py-1 text-[11px] font-semibold capitalize text-purple-100"
                            >
                              {emotion} {intensity.toFixed(0)}%
                            </span>
                          ))}
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{new Date(entry.timestamp).toLocaleString()}</p>
                    </article>
                  ))}
              </div>
            )}
          </section>

          {hasArtifacts && (
            <section className="md:col-span-2 rounded-2xl border border-purple-500/20 bg-slate-900/60 p-6 backdrop-blur">
              <div className="mb-4 flex items-center gap-2">
                <Share2 className="h-6 w-6 text-pink-400" />
                <h2 className="text-xl font-semibold">Emotional Artifacts</h2>
              </div>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                {artifacts
                  .slice()
                  .reverse()
                  .map((artifact) => (
                    <div key={artifact.id} className="group relative overflow-hidden rounded-xl border border-purple-500/30">
                      <img src={artifact.data} alt="Emotional artifact" className="h-auto w-full" />
                      <button
                        type="button"
                        onClick={() => downloadArtifact(artifact.data)}
                        className={cn(
                          'absolute inset-0 flex items-center justify-center bg-black/70 text-white transition-opacity',
                          'opacity-0 group-hover:opacity-100',
                        )}
                        aria-label="Download emotional artifact"
                      >
                        <Download className="h-7 w-7" />
                      </button>
                    </div>
                  ))}
              </div>
            </section>
          )}
        </div>

        <canvas ref={canvasRef} className="hidden" />
      </div>
    </div>
  );
}
