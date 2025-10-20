How to run:


cd packages/mirror-sync
pip install -e .
python -m playwright install
python -m mirror_sync

On first run, Mirror will ask you to Connect Wallet → approve in your wallet → you’re in.

The script stops at draft; you click Publish and sign.

Set `MIRROR_SYNC_SKIP_BROWSER=1` to render drafts without opening Mirror (useful in CI).
Set `MIRROR_SYNC_HEADLESS=1` to run the browser without a window.

No keys leave your machine. Echo never touches secrets.
