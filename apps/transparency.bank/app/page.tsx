"use client";

import { useEffect } from "react";
import useSWR from "swr";
import DataPanel from "../components/DataPanel";
import ProofBundleList from "../components/ProofBundleList";
import RealtimeFeed from "../components/RealtimeFeed";
import { fetchSnapshot } from "../lib/api";
import type { TransparencySnapshot } from "../lib/types";

export default function HomePage() {
  const { data, error, mutate } = useSWR<TransparencySnapshot>("/api/status", fetchSnapshot, {
    refreshInterval: 30000,
    revalidateOnFocus: false,
  });

  useEffect(() => {
    const source = new EventSource("/api/stream");
    source.onmessage = (event) => {
      try {
        const payload: TransparencySnapshot = JSON.parse(event.data);
        mutate(payload, { revalidate: false });
      } catch (err) {
        console.error("Failed to parse transparency event", err);
      }
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [mutate]);

  if (error) {
    return (
      <section className="panel error">
        <h2>Portal Error</h2>
        <p>Unable to reach transparency feed. Check the Express API logs.</p>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="panel loading">
        <h2>Loading transparency snapshot…</h2>
        <p>The portal is stitching the latest ledger, compliance, and governance data.</p>
      </section>
    );
  }

  return (
    <div className="grid">
      <DataPanel title="Inflows" entries={data.inflows} variant="inflow" />
      <DataPanel title="Outflows" entries={data.outflows} variant="outflow" />
      <DataPanel title="Compliance Credentials" entries={data.compliance} variant="compliance" />
      <DataPanel title="Governance Amendments" entries={data.governance} variant="governance" />
      <RealtimeFeed auditTrail={data.auditTrail} updatedAt={data.updatedAt} />
      <ProofBundleList proofBundles={data.proofBundles} opentimestamps={data.opentimestamps} />
    </div>
  );
}
