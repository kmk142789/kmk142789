# Echo Control Nexus

A Tailwind-powered Next.js dashboard that unifies EchoOS control center telemetry, Echo Computer sandbox logs, puzzle solution archives, and Neon banking automation.

## Getting started

1. Install dependencies:

   ```bash
   npm install
   npm install --prefix apps/echo-dashboard
   ```

2. Start the API gateway:

   ```bash
   npm run apps:echo-dashboard:api
   ```

   Configure the following environment variables when required:

   - `NEON_DATABASE_URL` – Postgres connection string (Neon).
   - `NEON_KEY_ENCRYPTION_KEY` – at least 16 characters for AES-256-GCM envelope encryption.
   - `ECHO_DASHBOARD_PORT` – optional port override.

3. Launch the web dashboard in a separate terminal:

   ```bash
   npm run apps:echo-dashboard:web
   ```

   By default, the frontend expects the API at `http://localhost:5050`. Override with `NEXT_PUBLIC_ECHO_API_BASE_URL`.

## Panels

- **Echo Computer Logs** – browse `logs/*.md` or `.log` files with inline previews.
- **Puzzle Solutions** – surface manuscripts from `puzzle_solutions/`.
- **Echo CLI Bridge** – execute curated `echo_cli` commands (`refresh`, `verify`, `stats`, `enrich-ud`, `export`, `transcend`).
- **Neon Vault** – encrypted storage for Neon API keys backed by Postgres.

## Production notes

- All Neon secrets are encrypted client-side using AES-256-GCM before database persistence.
- CLI invocations are time-boxed (45s) and limited to a fixed allow-list.
- API responses are CORS-enabled to support local development with `next dev`.
