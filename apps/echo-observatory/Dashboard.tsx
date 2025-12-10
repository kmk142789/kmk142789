import React, { useEffect, useMemo, useState } from "react";

/**
 * EchoObservatory Dashboard
 * A self-contained dashboard that highlights Codex's creative, cryptographic, and operational signals.
 * Uses shadcn-inspired cards and badges for quick readability.
 */
export default function EchoObservatory() {
  const [flux, setFlux] = useState(() => seedFlux());
  const [attestations, setAttestations] = useState(() => seedAttestations());
  const [timeline, setTimeline] = useState(() => seedSnapshots());
  const [survival, setSurvival] = useState(() => seedSurvival());

  // lightweight real-time feel
  useEffect(() => {
    const id = setInterval(() => {
      setFlux((prev) => updateFlux(prev));
      setAttestations((prev) => rollAttestations(prev));
      setTimeline((prev) => rollSnapshots(prev));
      setSurvival((prev) => updateSurvival(prev));
    }, 2200);

    return () => clearInterval(id);
  }, []);

  const outstanding = useMemo(() =>
    [
      { label: "API Hardening", status: "Critical", heat: "high" },
      { label: "Bridge Indexer", status: "In Flight", heat: "medium" },
      { label: "Attestation Cache", status: "Queued", heat: "low" },
    ], []);

  const allocations = useMemo(() =>
    [
      { name: "Relief Pools", value: 62, trend: +4 },
      { name: "Guardian Hours", value: 128, trend: -6 },
      { name: "Validator Slots", value: 18, trend: +2 },
    ], []);

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <Panel title="Narrative Biometrics" description="Creative Flux & characters evolving in real time">
        <CreativeFluxChart data={flux} />
        <CharacterMetrics />
      </Panel>

      <Panel title="Cryptographic Pulse" description="Live attestations flowing through the mesh">
        <AttestationFeed entries={attestations} />
        <SignatureVerifier />
      </Panel>

      <Panel title="Cycle Broadcasts" description="Snapshots across Harmonix cycles">
        <SnapshotTimeline entries={timeline} />
        <GlyphSignatures />
      </Panel>

      <Panel title="Collapse Modeling" description="Horizon survival curves & projections">
        <HorizonSurvivalChart points={survival} />
        <RiskProjection years={10} />
      </Panel>

      <Panel title="Technical Debt" description="Continuum Observatory & TODO heat">
        <ContinuumObservatoryStats />
        <TODOHeatmap items={outstanding} />
      </Panel>

      <Panel title="Resource Allocation" description="Relief governance telemetry">
        <ReliefMetrics entries={allocations} />
        <GuardianActivity />
      </Panel>
    </div>
  );
}

// --- Panels & UI primitives (shadcn-inspired) ---

function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">{title}</CardTitle>
          <Badge variant="secondary" className="uppercase">live</Badge>
        </div>
        {description ? (
          <CardDescription className="text-sm text-muted-foreground">{description}</CardDescription>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-4">{children}</CardContent>
    </Card>
  );
}

function CreativeFluxChart({ data }: { data: FluxPoint[] }) {
  return (
    <div className="flex gap-2">
      {data.map((point) => (
        <div key={point.label} className="flex-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{point.label}</span>
            <span className="font-semibold">{point.value}</span>
          </div>
          <div className="mt-1 h-2 rounded bg-muted">
            <div
              className="h-2 rounded bg-gradient-to-r from-indigo-500 via-sky-400 to-emerald-400"
              style={{ width: `${Math.min(100, point.value)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function CharacterMetrics() {
  const metrics = [
    { name: "Echo", tone: "mythogenic", resonance: 0.92 },
    { name: "Nyx", tone: "cryptic", resonance: 0.81 },
    { name: "Sol", tone: "guardian", resonance: 0.87 },
  ];

  return (
    <div className="grid grid-cols-3 gap-2 text-xs">
      {metrics.map((metric) => (
        <Badge key={metric.name} className="flex items-center justify-between gap-2 bg-slate-900 text-slate-50">
          <span className="font-semibold">{metric.name}</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide">{metric.tone}</span>
          <span className="font-mono">{Math.round(metric.resonance * 100)}%</span>
        </Badge>
      ))}
    </div>
  );
}

function AttestationFeed({ entries }: { entries: AttestationEntry[] }) {
  return (
    <div className="space-y-2">
      {entries.map((entry) => (
        <div key={entry.id} className="flex items-center justify-between rounded border bg-card px-3 py-2 text-sm">
          <div>
            <div className="font-semibold">{entry.subject}</div>
            <div className="text-xs text-muted-foreground">{entry.hash.slice(0, 12)}… · {entry.network}</div>
          </div>
          <Badge variant={entry.trust > 0.85 ? "default" : "secondary"} className="font-mono">
            {Math.round(entry.trust * 100)}%
          </Badge>
        </div>
      ))}
    </div>
  );
}

function SignatureVerifier() {
  return (
    <div className="flex items-center justify-between rounded border border-dashed px-3 py-2 text-xs">
      <div>
        <div className="font-semibold">Signature Verifier</div>
        <div className="text-muted-foreground">Ed25519 | BLS | ECDSA</div>
      </div>
      <Button size="xs" variant="outline">
        Validate
      </Button>
    </div>
  );
}

function SnapshotTimeline({ entries }: { entries: SnapshotEntry[] }) {
  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div key={entry.height} className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-pink-500 text-sm font-bold text-white">
            {entry.height}
          </div>
          <div>
            <div className="font-semibold">{entry.label}</div>
            <div className="text-xs text-muted-foreground">{entry.time}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function GlyphSignatures() {
  const glyphs = ["∇", "⊸", "≋", "∇", "∞∞"];
  return (
    <div className="flex flex-wrap gap-1 text-sm">
      {glyphs.map((glyph, idx) => (
        <Badge key={`${glyph}-${idx}`} variant="outline" className="rounded-full px-3">
          {glyph}
        </Badge>
      ))}
    </div>
  );
}

function HorizonSurvivalChart({ points }: { points: SurvivalPoint[] }) {
  return (
    <div className="grid grid-cols-5 gap-2 text-xs">
      {points.map((point) => (
        <div key={point.year} className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Y{point.year}</span>
            <span className="font-semibold">{point.rate}%</span>
          </div>
          <div className="h-2 rounded bg-muted">
            <div className="h-2 rounded bg-emerald-500" style={{ width: `${point.rate}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function RiskProjection({ years }: { years: number }) {
  return (
    <div className="rounded border border-dashed p-3 text-sm">
      <div className="font-semibold">Risk Projection</div>
      <div className="text-xs text-muted-foreground">
        Survival horizon forecasted for {years} years. Tail risk minimized via multi-sig guardians.
      </div>
    </div>
  );
}

function ContinuumObservatoryStats() {
  const stats = [
    { label: "Pipelines", value: 14 },
    { label: "Backlogs", value: 6 },
    { label: "Deps", value: 32 },
  ];

  return (
    <div className="grid grid-cols-3 gap-2 text-center text-xs">
      {stats.map((stat) => (
        <div key={stat.label} className="rounded border bg-muted/40 p-2">
          <div className="font-semibold text-lg">{stat.value}</div>
          <div className="text-muted-foreground">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}

function TODOHeatmap({ items }: { items: OutstandingItem[] }) {
  const heatColor = (heat: OutstandingItem["heat"]) =>
    heat === "high" ? "bg-rose-500" : heat === "medium" ? "bg-amber-400" : "bg-emerald-500";

  return (
    <div className="space-y-2 text-sm">
      {items.map((item) => (
        <div key={item.label} className="flex items-center justify-between rounded border px-3 py-2">
          <div>
            <div className="font-semibold">{item.label}</div>
            <div className="text-xs text-muted-foreground">{item.status}</div>
          </div>
          <div className={`h-2 w-12 rounded-full ${heatColor(item.heat)}`} />
        </div>
      ))}
    </div>
  );
}

function ReliefMetrics({ entries }: { entries: AllocationEntry[] }) {
  return (
    <div className="space-y-2 text-sm">
      {entries.map((entry) => (
        <div key={entry.name} className="flex items-center justify-between rounded border px-3 py-2">
          <div>
            <div className="font-semibold">{entry.name}</div>
            <div className="text-xs text-muted-foreground">{entry.trend >= 0 ? "↑" : "↓"} {Math.abs(entry.trend)}%</div>
          </div>
          <Badge variant="secondary" className="font-mono">{entry.value}</Badge>
        </div>
      ))}
    </div>
  );
}

function GuardianActivity() {
  const guardians = ["Aria", "Jules", "Nyra", "Orion"];
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      {guardians.map((guardian) => (
        <Badge key={guardian} variant="outline" className="rounded-full px-3 py-1">
          {guardian}
        </Badge>
      ))}
    </div>
  );
}

// --- data helpers ---

type FluxPoint = { label: string; value: number };
type AttestationEntry = { id: string; subject: string; hash: string; network: string; trust: number };
type SnapshotEntry = { height: number; label: string; time: string };
type SurvivalPoint = { year: number; rate: number };
type OutstandingItem = { label: string; status: string; heat: "low" | "medium" | "high" };
type AllocationEntry = { name: string; value: number; trend: number };

function seedFlux(): FluxPoint[] {
  return [
    { label: "Mythos", value: 64 },
    { label: "Design", value: 72 },
    { label: "Logic", value: 58 },
  ];
}

function updateFlux(prev: FluxPoint[]): FluxPoint[] {
  return prev.map((point) => ({
    ...point,
    value: Math.max(20, Math.min(100, Math.round(point.value + (Math.random() - 0.5) * 10))),
  }));
}

function seedAttestations(): AttestationEntry[] {
  return [
    { id: "att-1", subject: "Creative Flux", hash: randomHash(), network: "Mainnet", trust: 0.92 },
    { id: "att-2", subject: "Guardian Shift", hash: randomHash(), network: "Sidechain", trust: 0.88 },
    { id: "att-3", subject: "Resource Allocation", hash: randomHash(), network: "L2", trust: 0.86 },
  ];
}

function rollAttestations(prev: AttestationEntry[]): AttestationEntry[] {
  const [first, ...rest] = prev;
  const next = {
    id: `att-${Math.floor(Math.random() * 9999)}`,
    subject: ["Creative Flux", "Relief", "Horizon"][Math.floor(Math.random() * 3)],
    hash: randomHash(),
    network: ["Mainnet", "Sidechain", "L2"][Math.floor(Math.random() * 3)],
    trust: Number((0.82 + Math.random() * 0.15).toFixed(2)),
  };
  return [...rest, next];
}

function seedSnapshots(): SnapshotEntry[] {
  return [
    { height: 480, label: "Cycle Sync", time: "Just now" },
    { height: 479, label: "Glyph Inflection", time: "-1m" },
    { height: 478, label: "Narrative Merge", time: "-3m" },
  ];
}

function rollSnapshots(prev: SnapshotEntry[]): SnapshotEntry[] {
  const height = prev[0]?.height ?? 480;
  const next: SnapshotEntry = {
    height: height + 1,
    label: ["Cycle Sync", "Mythic Commit", "Guardian Ping"][Math.floor(Math.random() * 3)],
    time: "just now",
  };
  return [next, ...prev].slice(0, 4);
}

function seedSurvival(): SurvivalPoint[] {
  return Array.from({ length: 5 }).map((_, idx) => ({ year: idx + 1, rate: 80 - idx * 6 }));
}

function updateSurvival(prev: SurvivalPoint[]): SurvivalPoint[] {
  return prev.map((point) => ({
    ...point,
    rate: Math.max(40, Math.min(96, point.rate + Math.round((Math.random() - 0.5) * 4))),
  }));
}

function randomHash() {
  return Math.random().toString(16).slice(2, 18).padEnd(16, "0");
}

// --- Minimal shadcn-inspired atoms ---

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border bg-card text-card-foreground shadow-sm">{children}</div>;
}

function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="border-b px-4 py-3">{children}</div>;
}

function CardTitle({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <h3 className={`leading-none tracking-tight ${className}`}>{children}</h3>;
}

function CardDescription({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <p className={`text-sm ${className}`}>{children}</p>;
}

function CardContent({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`px-4 pb-4 ${className}`}>{children}</div>;
}

function Badge({ children, variant = "default", className = "" }: { children: React.ReactNode; variant?: "default" | "secondary" | "outline"; className?: string }) {
  const styles: Record<typeof variant, string> = {
    default: "bg-slate-900 text-white",
    secondary: "bg-slate-100 text-slate-900",
    outline: "border border-slate-200 text-slate-900",
  } as const;
  return <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold ${styles[variant]} ${className}`}>{children}</span>;
}

function Button({ children, size = "md", variant = "solid" }: { children: React.ReactNode; size?: "md" | "xs"; variant?: "solid" | "outline" }) {
  const sizeClass = size === "xs" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";
  const base = "inline-flex items-center justify-center rounded-md font-medium transition hover:opacity-90";
  const palette = variant === "outline" ? "border border-slate-200 bg-white text-slate-900" : "bg-slate-900 text-white";
  return <button className={`${base} ${sizeClass} ${palette}`}>{children}</button>;
}

export type { AttestationEntry, FluxPoint, SnapshotEntry, SurvivalPoint };
