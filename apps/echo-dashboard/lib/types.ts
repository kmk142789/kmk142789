export interface FileDescriptor {
  name: string;
  preview?: string;
  content?: string;
}

export interface LogChunkDescriptor {
  name: string;
  chunk: string;
  start: number;
  end: number;
  size: number;
  hasMoreBackward: boolean;
  hasMoreForward: boolean;
  previousCursor: number | null;
  nextCursor: number | null;
}

export interface PuzzleAttestation {
  puzzle_id: number;
  payload: Record<string, unknown>;
  checksum: string;
  base58: string;
  ts: string;
  record_hash?: string;
  created_at?: string;
  stored?: boolean;
}

export interface PuzzleFileDescriptor extends FileDescriptor {
  puzzle_id?: number | null;
  attestation?: PuzzleAttestation | null;
}

export interface CliCommand {
  value: string;
  label: string;
}

export interface CliResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

export interface NeonKeyRecord {
  id: string;
  label: string;
  last_four: string;
  created_at: string;
}

export interface CodexItem {
  id: number;
  title: string;
  summary: string;
  labels: string[];
  url: string;
  merged_at: string;
  hash: string;
}

export interface CodexRegistryResponse {
  version: number;
  generated_at: string;
  items: CodexItem[];
  repository?: string;
}

export interface MetricSeriesPoint {
  ts: string;
  value: number;
}

export interface MetricGroup {
  label: string;
  total: number;
  series: MetricSeriesPoint[];
}

export interface MetricsOverview {
  range: {
    from: string;
    to: string;
  };
  metrics: {
    codexMerges: MetricGroup;
    puzzleSolutions: MetricGroup;
    logVolume: MetricGroup;
    attestationStored: MetricGroup | null;
  };
}

export interface AssistantResponse {
  success: boolean;
  message: string;
  function: string;
  arguments: Record<string, unknown>;
  data: Record<string, unknown> | null;
  logs: string[];
}

export interface Wallet {
  id: string;
  chain: string;
  address: string;
  label: string;
  verified: boolean;
  signature?: string;
  explorerUrl?: string;
  balance?: number;
  updatedAt: string;
}
