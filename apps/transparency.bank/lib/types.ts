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
