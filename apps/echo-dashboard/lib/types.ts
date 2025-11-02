export interface FileDescriptor {
  name: string;
  preview?: string;
  content?: string;
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

export interface AssistantResponse {
  success: boolean;
  message: string;
  function: string;
  arguments: Record<string, unknown>;
  data: Record<string, unknown> | null;
  logs: string[];
}
