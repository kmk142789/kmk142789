export interface FileDescriptor {
  name: string;
  preview?: string;
  content?: string;
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
