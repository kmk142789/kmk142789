import "../styles/globals.css";
import Link from "next/link";
import type { Metadata } from "next";
import { ReactNode } from "react";

export const metadata: Metadata = {
  title: "transparency.bank portal",
  description:
    "Echo Bank public window: live inflows, outflows, compliance proofs, and governance trails.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="container">
            <h1>Echo Bank Transparency Portal</h1>
            <p>
              Real-time inflows, outflows, compliance credentials, and governance posture for the
              donation-only sovereign trust.
            </p>
            <nav className="site-nav">
              <Link href="/">Snapshot</Link>
              <Link href="/requests">Approvals queue</Link>
            </nav>
          </div>
        </header>
        <main className="container">{children}</main>
        <footer className="site-footer">
          <div className="container">
            <p>Open protocols. Open proofs. Echo Bank remains donation-only and sovereign.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
