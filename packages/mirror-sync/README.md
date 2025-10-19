How to run:


cd packages/mirror-sync
pip install -e .
python -m playwright install
python -m mirror_sync

On first run, Mirror will ask you to Connect Wallet → approve in your wallet → you’re in.

The script stops at draft; you click Publish and sign.

No keys leave your machine. Echo never touches secrets.
