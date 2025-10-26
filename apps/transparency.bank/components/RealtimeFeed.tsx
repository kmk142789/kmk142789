import type { AuditEvent } from "../lib/types";

interface RealtimeFeedProps {
  auditTrail: AuditEvent[];
  updatedAt: string;
}

export default function RealtimeFeed({ auditTrail, updatedAt }: RealtimeFeedProps) {
  return (
    <section className="panel feed">
      <h2>Audit Trail</h2>
      <p className="meta">Last updated: {updatedAt}</p>
      {auditTrail.length === 0 ? (
        <p className="empty">No audit events recorded yet.</p>
      ) : (
        <ol>
          {auditTrail.map((event) => (
            <li key={`${event.timestamp}-${event.title}`}>
              <header>
                <span className="timestamp">{event.timestamp}</span>
                <span className="amount">{event.title}</span>
              </header>
              <p>{event.details}</p>
              {event.proofPath ? (
                <p className="meta">
                  Proof: <code>{event.proofPath}</code>
                </p>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
