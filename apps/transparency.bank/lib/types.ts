export interface LedgerEntrySummary {
  id: string;
  timestamp: string;
  narrative: string;
  amount?: string;
  asset?: string;
  account?: string;
  digest?: string;
  classification?: string;
  credentialPath?: string;
  link?: string;
}

export interface GovernanceAmendment {
  title: string;
  summary: string;
  reference: string;
  timestamp: string;
}

export interface AuditEvent {
  title: string;
  details: string;
  proofPath?: string;
  timestamp: string;
}

export interface ProofBundleInfo {
  path: string;
  digest?: string;
  direction?: string;
  asset?: string;
  otsReceipt?: string;
}

export interface OpenTimestampLink {
  label: string;
  path: string;
}

export interface TransparencySnapshot {
  updatedAt: string;
  inflows: LedgerEntrySummary[];
  outflows: LedgerEntrySummary[];
  compliance: LedgerEntrySummary[];
  governance: GovernanceAmendment[];
  auditTrail: AuditEvent[];
  proofBundles: ProofBundleInfo[];
  opentimestamps: OpenTimestampLink[];
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

export interface TimelineEvent {
  who: string;
  what: string;
  when: string;
}

export interface SpendRequest {
  id: string;
  payee: string;
  amount: number;
  category: 'Housing' | 'Program' | 'Ops' | 'Reserve';
  purpose: string;
  sourceHint?: string;
  attachments: string[];
  status: 'Pending' | 'Approved' | 'Rejected';
  requester: string;
  approver1?: string;
  approver2?: string;
  timeline: TimelineEvent[];
  createdAt: string;
}

export interface LedgerEntry {
  id: string;
  dateISO: string;
  kind: 'INFLOW' | 'DISBURSE';
  amount: number;
  category: string;
  payee: string;
  ref?: string;
  tx?: string;
  notes?: string;
}

export interface Policy {
  id: string;
  selfApproveMax: number;
  dualApproveMin: number;
  governanceMin: number;
  cashWithdrawalCap: number;
}

export interface Snapshot {
  id: string;
  treasuryUSD: number;
  reserveUSD: number;
  programUSD: number;
  deltaUSD: number;
}
