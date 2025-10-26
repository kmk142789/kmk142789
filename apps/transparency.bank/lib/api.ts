import type { TransparencySnapshot } from "./types";

export async function fetchSnapshot(url: string): Promise<TransparencySnapshot> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Transparency API responded with ${response.status}`);
  }
  return (await response.json()) as TransparencySnapshot;
}
