"use client";

import { FormEvent, useMemo, useState } from "react";
import type { Policy, SpendRequest, TimelineEvent } from "../lib/types";

interface RequestsScreenProps {
  requests: SpendRequest[];
  policy: Policy;
  onAddRequest: (request: SpendRequest) => void;
  onApprove: (id: string, approver: string) => void;
  onReject: (id: string, approver: string) => void;
  onMarkPaid: (id: string, tx: string, notes: string) => void;
}

interface RequestCardProps {
  request: SpendRequest;
  policy: Policy;
  onClick: () => void;
}

interface NewRequestModalProps {
  policy: Policy;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onClose: () => void;
}

interface RequestDetailModalProps {
  request: SpendRequest;
  policy: Policy;
  onApprove: (id: string, approver: string) => void;
  onReject: (id: string, approver: string) => void;
  onMarkPaid: (id: string, tx: string, notes: string) => void;
  onClose: () => void;
}

const spendCategories: SpendRequest["category"][] = ["Housing", "Program", "Ops", "Reserve"];

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

export default function RequestsScreen({
  policy,
  requests,
  onAddRequest,
  onApprove,
  onReject,
  onMarkPaid,
}: RequestsScreenProps) {
  const [showNewForm, setShowNewForm] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);

    const payee = formData.get("payee");
    const amountValue = formData.get("amount");
    const categoryValue = formData.get("category");
    const purpose = formData.get("purpose");
    const sourceHint = formData.get("sourceHint");

    if (typeof payee !== "string" || !payee.trim()) {
      return;
    }

    if (typeof amountValue !== "string" || !amountValue.trim()) {
      return;
    }

    if (typeof purpose !== "string" || !purpose.trim()) {
      return;
    }

    const amount = Number.parseFloat(amountValue);
    if (!Number.isFinite(amount) || amount <= 0) {
      return;
    }

    if (typeof categoryValue !== "string" || !spendCategories.includes(categoryValue as SpendRequest["category"])) {
      return;
    }

    const now = new Date().toISOString();

    const request: SpendRequest = {
      id: `req-${Date.now()}`,
      payee: payee.trim(),
      amount,
      category: categoryValue as SpendRequest["category"],
      purpose: purpose.trim(),
      sourceHint: typeof sourceHint === "string" && sourceHint.trim() ? sourceHint.trim() : undefined,
      attachments: [],
      status: "Pending",
      requester: "Steward A",
      timeline: [
        {
          who: "Steward A",
          what: "Requested",
          when: now,
        },
      ],
      createdAt: now,
    };

    onAddRequest(request);
    setShowNewForm(false);
    form.reset();
  };

  const selected = useMemo(
    () => requests.find((request) => request.id === selectedRequest) ?? null,
    [requests, selectedRequest],
  );

  return (
    <section className="requests-shell">
      <header className="requests-header">
        <div>
          <h1>Approvals Queue</h1>
          <p className="requests-subtitle">Track spending approvals, policy thresholds, and payment status.</p>
        </div>
        <button type="button" className="requests-new-button" onClick={() => setShowNewForm(true)}>
          New request
        </button>
      </header>

      {requests.length === 0 ? (
        <p className="request-empty">No spend requests yet. Submit a new request to begin the approval flow.</p>
      ) : (
        <div className="request-list">
          {requests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              policy={policy}
              onClick={() => setSelectedRequest(request.id)}
            />
          ))}
        </div>
      )}

      {showNewForm && <NewRequestModal policy={policy} onSubmit={handleSubmit} onClose={() => setShowNewForm(false)} />}

      {selected && (
        <RequestDetailModal
          request={selected}
          policy={policy}
          onApprove={onApprove}
          onReject={onReject}
          onMarkPaid={onMarkPaid}
          onClose={() => setSelectedRequest(null)}
        />
      )}
    </section>
  );
}

function RequestCard({ policy, request, onClick }: RequestCardProps) {
  const needsDualApproval = request.amount >= policy.dualApproveMin;
  const hasFirstApproval = Boolean(request.approver1);
  const needsSecondApproval =
    request.status === "Pending" && needsDualApproval && hasFirstApproval && !request.approver2;

  const summary = request.purpose.length > 84 ? `${request.purpose.slice(0, 84)}…` : request.purpose;

  return (
    <article className="request-card" onClick={onClick} role="button" tabIndex={0} onKeyDown={(event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onClick();
      }
    }}>
      <header className="request-card-heading">
        <div>
          <div className="request-payee">{request.payee}</div>
          <div className="request-category">{request.category}</div>
        </div>
        <div className="request-statuses">
          <span className={`request-status request-status-${request.status.toLowerCase()}`}>{request.status}</span>
          {needsSecondApproval && <span className="request-status-secondary">Needs second approval</span>}
        </div>
      </header>
      <div className="request-amount">{currencyFormatter.format(request.amount)}</div>
      <p className="request-purpose">{summary}</p>
      <footer className="request-meta">
        <span>Requested by {request.requester}</span>
        <span>{new Date(request.createdAt).toLocaleDateString()}</span>
      </footer>
    </article>
  );
}

function NewRequestModal({ onClose, onSubmit, policy }: NewRequestModalProps) {
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="new-request-title">
      <div className="modal-sheet">
        <header className="modal-header">
          <h2 id="new-request-title">New spend request</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        <form className="request-form" onSubmit={onSubmit}>
          <label>
            Payee
            <input name="payee" type="text" required placeholder="Vendor or recipient name" />
          </label>
          <label>
            Amount (USD)
            <input name="amount" type="number" min="0" step="0.01" required placeholder="0.00" />
          </label>
          <label>
            Category
            <select name="category" required defaultValue="Housing">
              {spendCategories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          <label>
            Purpose
            <textarea name="purpose" required rows={4} placeholder="Describe what this request covers" />
          </label>
          <label>
            Source hint (optional)
            <input name="sourceHint" type="text" placeholder="Wallet, account, or funding source" />
          </label>

          <p className="request-policy-note">
            Policy thresholds: dual approval ≥ {currencyFormatter.format(policy.dualApproveMin)}, governance vote ≥ {" "}
            {currencyFormatter.format(policy.governanceMin)}, cash withdrawal cap {currencyFormatter.format(policy.cashWithdrawalCap)}.
          </p>

          <div className="modal-actions">
            <button type="button" className="button-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="button-primary">
              Submit request
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RequestDetailModal({ onApprove, onClose, onMarkPaid, onReject, policy, request }: RequestDetailModalProps) {
  const [showPaidForm, setShowPaidForm] = useState(false);
  const [tx, setTx] = useState("");
  const [notes, setNotes] = useState("");

  const needsDualApproval = request.amount >= policy.dualApproveMin;
  const needsGovernance = request.amount >= policy.governanceMin;
  const hasFirstApproval = Boolean(request.approver1);
  const awaitingSecondApproval = needsDualApproval && hasFirstApproval && !request.approver2;
  const canApprove = request.status === "Pending" && (!needsDualApproval || !hasFirstApproval || awaitingSecondApproval);

  const sortedTimeline = useMemo(
    () => [...request.timeline].sort((a, b) => a.when.localeCompare(b.when)),
    [request.timeline],
  );

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="request-detail-title">
      <div className="modal-sheet">
        <header className="modal-header">
          <h2 id="request-detail-title">Request details</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <div className="request-detail">
          <div>
            <span className="request-detail-label">Payee</span>
            <div className="request-detail-value">{request.payee}</div>
          </div>
          <div>
            <span className="request-detail-label">Amount</span>
            <div className="request-detail-value request-detail-amount">{currencyFormatter.format(request.amount)}</div>
          </div>
          <div>
            <span className="request-detail-label">Purpose</span>
            <p className="request-detail-text">{request.purpose}</p>
          </div>
          {request.sourceHint && (
            <div>
              <span className="request-detail-label">Source hint</span>
              <p className="request-detail-text">{request.sourceHint}</p>
            </div>
          )}
          <div className="request-detail-approvals">
            <span className="request-detail-label">Approvals</span>
            <ul>
              <li>
                <strong>First:</strong> {request.approver1 ?? "Pending"}
              </li>
              {needsDualApproval && <li><strong>Second:</strong> {request.approver2 ?? "Pending"}</li>}
            </ul>
          </div>
        </div>

        {needsGovernance && (
          <div className="request-governance-banner" role="note">
            Governance vote required for requests ≥ {currencyFormatter.format(policy.governanceMin)}.
          </div>
        )}

        <section className="request-timeline">
          <h3>Timeline</h3>
          <ol>
            {sortedTimeline.map((event: TimelineEvent, index: number) => (
              <li key={`${event.when}-${index}`}>
                <span className="timeline-action">{event.what}</span>
                <span className="timeline-meta">{event.who}</span>
                <time className="timeline-time">{new Date(event.when).toLocaleString()}</time>
              </li>
            ))}
          </ol>
        </section>

        {canApprove && (
          <div className="modal-actions">
            <button
              type="button"
              className="button-success"
              onClick={() => {
                onApprove(request.id, hasFirstApproval ? "Steward C" : "Steward B");
                onClose();
              }}
            >
              Approve
            </button>
            <button
              type="button"
              className="button-danger"
              onClick={() => {
                onReject(request.id, hasFirstApproval ? "Steward C" : "Steward B");
                onClose();
              }}
            >
              Reject
            </button>
          </div>
        )}

        {request.status === "Approved" && !showPaidForm && (
          <div className="modal-actions">
            <button type="button" className="button-primary" onClick={() => setShowPaidForm(true)}>
              Mark as paid
            </button>
          </div>
        )}

        {showPaidForm && (
          <form
            className="request-paid-form"
            onSubmit={(event) => {
              event.preventDefault();
              onMarkPaid(request.id, tx.trim(), notes.trim());
              setShowPaidForm(false);
              setTx("");
              setNotes("");
              onClose();
            }}
          >
            <label>
              TX / ACH reference
              <input value={tx} onChange={(event) => setTx(event.target.value)} placeholder="Optional transaction reference" />
            </label>
            <label>
              Notes
              <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Optional notes" />
            </label>
            <div className="modal-actions">
              <button type="submit" className="button-success">
                Confirm paid
              </button>
              <button
                type="button"
                className="button-secondary"
                onClick={() => {
                  setShowPaidForm(false);
                  setTx("");
                  setNotes("");
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className="modal-actions">
          <button type="button" className="button-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
