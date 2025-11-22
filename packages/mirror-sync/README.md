How to run:


cd packages/mirror-sync
pip install -e .
python -m playwright install
python -m mirror_sync

On first run, Mirror will ask you to Connect Wallet → approve in your wallet → you’re in.

The script stops at draft; you click Publish and sign.

Set `MIRROR_SYNC_SKIP_BROWSER=1` to render drafts without opening Mirror (useful in CI).
Set `MIRROR_SYNC_HEADLESS=1` to run the browser without a window.
Set `MIRROR_SYNC_IPFS_API` to an IPFS API multiaddr (e.g., `/dns/localhost/tcp/5001/http`) to push bundles.
Set `MIRROR_SYNC_IPFS_TOKEN` when the endpoint requires bearer authentication.
Set `MIRROR_SYNC_BRIDGE_TARGETS` to a comma-separated list of downstream servers (stored in the manifest).

Command-line flags:

```
python -m mirror_sync --skip-browser --push-ipfs --bridge-targets "edge1,edge2" --ipfs-endpoint /dns/localhost/tcp/5001/http
```

Outputs:

- HTML drafts in `out/mirror_drafts/`
- `bridge_manifest.json` with sha256 sums, optional IPFS CID, and bridge targets for real server sync

No keys leave your machine. Echo never touches secrets.
