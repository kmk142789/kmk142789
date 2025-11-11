import type { GovernanceAmendment, LedgerEntrySummary } from "../lib/types";
import ExportLedgerButton from "./ExportLedgerButton";

type Variant = "inflow" | "outflow" | "compliance" | "governance";

type PanelEntry = LedgerEntrySummary | GovernanceAmendment;

interface DataPanelProps {
  title: string;
  entries: PanelEntry[];
  variant: Variant;
}

const variantClassMap: Record<Variant, string> = {
  inflow: "panel inflow",
  outflow: "panel outflow",
  compliance: "panel compliance",
  governance: "panel governance",
};

function isGovernance(entry: PanelEntry): entry is GovernanceAmendment {
  return (entry as GovernanceAmendment).reference !== undefined;
}

function renderLedger(entry: LedgerEntrySummary) {
  return (
    <li key={entry.id}>
      <header>
        <span className="timestamp">{entry.timestamp}</span>
        {entry.amount && entry.asset ? (
          <span className="amount">
            {entry.amount} {entry.asset}
          </span>
        ) : null}
      </header>
      <p>{entry.narrative}</p>
      {entry.account ? <p className="meta">Account: {entry.account}</p> : null}
      {entry.digest ? <p className="meta">Digest: {entry.digest}</p> : null}
      {entry.classification ? <p className="meta">Classification: {entry.classification}</p> : null}
      {entry.credentialPath ? (
        <p className="meta">
          Credential: <code>{entry.credentialPath}</code>
        </p>
      ) : null}
      {entry.link ? (
        <p className="meta">
          <a href={entry.link} target="_blank" rel="noreferrer">
            Proof bundle
          </a>
        </p>
      ) : null}
    </li>
  );
}

function renderGovernance(entry: GovernanceAmendment) {
  return (
    <li key={entry.reference}>
      <header>
        <span className="timestamp">{entry.timestamp}</span>
        <span className="amount">{entry.title}</span>
      </header>
      <p>{entry.summary}</p>
      <p className="meta">
        Reference: <code>{entry.reference}</code>
      </p>
    </li>
  );
}

export default function DataPanel({ title, entries, variant }: DataPanelProps) {
  const panelClass = variantClassMap[variant];
  const isLedgerVariant = variant === "inflow" || variant === "outflow" || variant === "compliance";
  const ledgerEntries = isLedgerVariant ? (entries as LedgerEntrySummary[]) : null;

  return (
    <section className={panelClass}>
      <div className="panel-heading">
        <h2>{title}</h2>
        {isLedgerVariant && ledgerEntries ? (
          <ExportLedgerButton entries={ledgerEntries} title={title} variant={variant} />
        ) : null}
      </div>
      {entries.length === 0 ? (
        <p className="empty">No entries yet.</p>
      ) : (
        <ul>
          {entries.map((entry) =>
            isGovernance(entry) ? renderGovernance(entry) : renderLedger(entry)
          )}
        </ul>
      )}
    </section>
  );
}
