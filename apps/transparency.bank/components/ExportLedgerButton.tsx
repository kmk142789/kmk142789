"use client";

import { useCallback, useMemo } from "react";

import type { LedgerEntrySummary } from "../lib/types";
import { exportLedgerToCSV } from "../lib/exportLedgerToCSV";

interface ExportLedgerButtonProps {
  entries: LedgerEntrySummary[];
  title: string;
  variant: "inflow" | "outflow" | "compliance";
}

export default function ExportLedgerButton({ entries, title, variant }: ExportLedgerButtonProps) {
  const filename = useMemo(() => {
    const normalisedTitle = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    const prefix = normalisedTitle || variant;
    return `${prefix}-ledger`;
  }, [title, variant]);

  const handleClick = useCallback(() => {
    exportLedgerToCSV(entries, filename);
  }, [entries, filename]);

  const disabled = entries.length === 0;

  return (
    <button type="button" className="export-button" onClick={handleClick} disabled={disabled}>
      Export CSV
    </button>
  );
}
