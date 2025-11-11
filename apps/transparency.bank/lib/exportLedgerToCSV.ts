import type { LedgerEntrySummary } from "./types";

const HEADERS = ["Date", "Type", "Amount", "Category", "Payee", "Reference", "Transaction", "Notes"] as const;

type Header = (typeof HEADERS)[number];

function escapeCell(value: string): string {
  const safe = value.replace(/"/g, '""');
  return `"${safe}"`;
}

function normaliseValue(value: string | null | undefined): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

function buildRow(entry: LedgerEntrySummary, fallbackType: string): Record<Header, string> {
  const date = new Date(entry.timestamp ?? Date.now()).toLocaleDateString();
  const type = entry.classification ?? fallbackType;
  const category = entry.classification ?? "";
  const payee = entry.account ?? "";
  const reference = entry.credentialPath ?? entry.digest ?? "";
  const transaction = entry.link ?? "";
  const notes = entry.narrative ?? "";
  const amount = entry.amount ? `${entry.amount}${entry.asset ? ` ${entry.asset}` : ""}` : entry.asset ?? "";

  return {
    Date: date,
    Type: type,
    Amount: amount,
    Category: category,
    Payee: payee,
    Reference: reference,
    Transaction: transaction,
    Notes: notes,
  };
}

export function exportLedgerToCSV(entries: LedgerEntrySummary[], filenamePrefix: string) {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }

  const rows = entries.map((entry) => buildRow(entry, filenamePrefix));

  const csvLines = [
    HEADERS.join(","),
    ...rows.map((row) => HEADERS.map((header) => escapeCell(normaliseValue(row[header]))).join(",")),
  ];

  const csvContent = csvLines.join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filenamePrefix}-${new Date().toISOString().split("T")[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
