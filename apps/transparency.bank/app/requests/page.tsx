"use client";

import { useMemo, useState } from "react";
import RequestsScreen from "../../components/RequestsScreen";
import { seedPolicy, seedRequests } from "../../lib/fixtures/seeds";
import type { Policy, SpendRequest } from "../../lib/types";

function cloneRequest(request: SpendRequest): SpendRequest {
  return {
    ...request,
    timeline: request.timeline.map((event) => ({ ...event })),
  };
}

export default function RequestsPage() {
  const [requests, setRequests] = useState<SpendRequest[]>(() => seedRequests.map(cloneRequest));
  const policy: Policy = useMemo(() => ({ ...seedPolicy }), []);

  const handleAddRequest = (request: SpendRequest) => {
    setRequests((prev) => [cloneRequest(request), ...prev]);
  };

  const handleApprove = (id: string, approver: string) => {
    setRequests((prev) =>
      prev.map((request) => {
        if (request.id !== id || request.status === "Rejected") {
          return request;
        }

        const now = new Date().toISOString();
        const needsDualApproval = request.amount >= policy.dualApproveMin;

        if (!request.approver1) {
          const firstApprovalEvent = needsDualApproval ? "First approval granted" : "Approved";
          return {
            ...request,
            approver1: approver,
            status: needsDualApproval ? "Pending" : "Approved",
            timeline: [...request.timeline, { who: approver, what: firstApprovalEvent, when: now }],
          };
        }

        if (needsDualApproval && !request.approver2) {
          return {
            ...request,
            approver2: approver,
            status: "Approved",
            timeline: [...request.timeline, { who: approver, what: "Second approval granted", when: now }],
          };
        }

        return request;
      }),
    );
  };

  const handleReject = (id: string, approver: string) => {
    setRequests((prev) =>
      prev.map((request) => {
        if (request.id !== id) {
          return request;
        }

        const now = new Date().toISOString();
        return {
          ...request,
          status: "Rejected",
          timeline: [...request.timeline, { who: approver, what: "Rejected", when: now }],
        };
      }),
    );
  };

  const handleMarkPaid = (id: string, tx: string, notes: string) => {
    setRequests((prev) =>
      prev.map((request) => {
        if (request.id !== id) {
          return request;
        }

        const now = new Date().toISOString();
        const details = tx ? `Marked paid (ref: ${tx})` : "Marked paid";
        const noteSuffix = notes ? ` — ${notes}` : "";

        return {
          ...request,
          timeline: [...request.timeline, { who: "Treasury Ops", what: `${details}${noteSuffix}`, when: now }],
        };
      }),
    );
  };

  return (
    <RequestsScreen
      policy={policy}
      requests={requests}
      onAddRequest={handleAddRequest}
      onApprove={handleApprove}
      onReject={handleReject}
      onMarkPaid={handleMarkPaid}
    />
  );
}
