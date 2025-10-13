## Offline UI
Open `verifier/ui/index.html` in your browser. Drag & drop `.attest/*.json` files to verify that each context’s SHA256 matches.

## Federation (canary)
```bash
docker compose -f docker-compose.federation.yml up --build -d
# Nodes: http://localhost:8101/health, :8102/health, :8103/health
```
