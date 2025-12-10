# Relief System Service

A hardened reference implementation for the Relief System schema and API. The service pairs a production-ready PostgreSQL layout with an Express server that handles authentication, governance-aware relief approvals, treasury summaries, metrics, and audit lookups.

## Contents
- `schema.sql` – PostgreSQL schema with audit triggers, password hashing column, and default governance rules.
- `server.mjs` – Express API with JWT auth, HMAC signing for relief events, and governance enforcement.
- `package.json` – Local dependencies so the service is isolated from the monorepo root.

## Quick start
1. **Install dependencies**
   ```bash
   cd services/relief_system
   npm install
   ```
2. **Create the database**
   ```bash
   psql -U relief_admin -d relief_system -f schema.sql
   ```
3. **Configure environment** via a `.env` file alongside `server.mjs`:
   ```env
   PORT=8080
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=relief_system
   DB_USER=relief_admin
   DB_PASSWORD=change-me
   JWT_SECRET=replace-with-64-char-secret
   JWT_REFRESH_SECRET=replace-with-64-char-refresh-secret
   SIGNING_SECRET=optional-hmac-secret
   ALLOWED_ORIGINS=http://localhost:3000
   ```
4. **Run the service**
   ```bash
   npm start
   ```

The seeded guardian in `schema.sql` uses the username `admin` with the bcrypt hash for the temporary password `ChangeMeNow!`. Rotate this immediately after provisioning.

## Security notes
- Passwords are validated with bcrypt hashes stored in the `guardians.password_hash` column.
- Governance limits are enforced at request time; multi-signature thresholds are derived from `governance_rules`.
- Audit entries are created for authentication, relief requests, and approvals to keep a tamper-evident trail.

## Health check
The `/health` endpoint responds with the current status and version so orchestration systems can monitor availability.
