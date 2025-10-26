import type { OpenTimestampLink, ProofBundleInfo } from "../lib/types";

interface ProofBundleListProps {
  proofBundles: ProofBundleInfo[];
  opentimestamps: OpenTimestampLink[];
}

export default function ProofBundleList({ proofBundles, opentimestamps }: ProofBundleListProps) {
  return (
    <section className="panel proofs">
      <h2>Proof Bundles &amp; OpenTimestamps</h2>
      {proofBundles.length === 0 ? (
        <p className="empty">No proof bundles have been published yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Bundle</th>
              <th>Digest</th>
              <th>Direction</th>
              <th>OTS</th>
            </tr>
          </thead>
          <tbody>
            {proofBundles.map((bundle) => (
              <tr key={bundle.path}>
                <td>
                  <code>{bundle.path}</code>
                </td>
                <td>{bundle.digest ?? "—"}</td>
                <td>{bundle.direction ?? "—"}</td>
                <td>{bundle.otsReceipt ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {opentimestamps.length > 0 ? (
        <div className="ots-links">
          <h3>OpenTimestamp Receipts</h3>
          <ul>
            {opentimestamps.map((link) => (
              <li key={link.path}>
                <a href={link.path} target="_blank" rel="noreferrer">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
