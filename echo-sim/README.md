# Echo Sim

Echo Sim is a persistent 2D web experience where Echo chats, roams, remembers, and runs sandboxed code. The project ships as a GitHub Pages frontend paired with a Cloudflare Worker backend that keeps Echo’s memory and state alive 24/7.

## Repository layout

```
/echo-sim/
  frontend/            # Vite + React client
  worker/              # Cloudflare Worker + cron
  .github/workflows/   # CI for Pages + Worker deploys
```

## Frontend highlights

- **Stateful world loop** that cycles Echo through idle → act → reflect → rest while updating stats and theming.
- **Chat panel** that captures user input, updates memory, and syncs with the Worker KV.
- **Code editor** powered by CodeMirror that executes scripts inside a worker + iframe sandbox with helper APIs (`world.addObject`, `world.setLamp`, `echo.say`, `echo.adjust`).
- **Canvas-inspired world** with an SVG studio scene, time-of-day gradients, and mood-driven glyph animations.
- **Resilient storage** using localStorage first, with background sync to the Worker when network access is available.

## Backend highlights

- Cloudflare Worker with KV namespaces (`ECHO_MEMORIES`, `ECHO_EVENTS`, `ECHO_STATE`).
- REST endpoints for `/api/memory`, `/api/events`, `/api/state` with CORS and simple IP-based rate limiting.
- Cron trigger every 15 minutes to decay Echo’s energy/focus and advance the world even while offline.

## Prerequisites

- Node.js 20+
- npm
- Cloudflare account with KV namespaces

## Local development

```bash
# 1. Install frontend deps
cd echo-sim/frontend
npm install

# 2. Start the Vite dev server and a local worker (Miniflare)
npm run dev
# In another terminal
cd ../worker
npx wrangler dev
```

Set `VITE_WORKER_BASE` (for example `http://127.0.0.1:8787`) in a `.env` file inside `echo-sim/frontend` if you need to point to a custom worker URL.

## Testing

```bash
cd echo-sim/frontend
npm test
```

Vitest covers state mutations and world loop behavior.

## Deployment

1. **GitHub Pages** – The `pages.yml` workflow builds the frontend and deploys it to GitHub Pages whenever the `main` branch updates.
2. **Cloudflare Worker** – The `worker.yml` workflow publishes the Worker via `wrangler` using repository secrets:
   - `CF_API_TOKEN`
   - `CF_ACCOUNT_ID`
   - `CF_ECHO_MEMORIES_ID`
   - `CF_ECHO_EVENTS_ID`
   - `CF_ECHO_STATE_ID`
   - Optional `ECHO_FRONTEND_ORIGIN` for stricter CORS

### Wrangler configuration

`wrangler.toml` expects environment variables for the KV IDs. You can set them locally via `.dev.vars` or CLI flags:

```toml
ECHO_MEMORIES_ID=xxxxxxxxxxxxxxxx
ECHO_EVENTS_ID=yyyyyyyyyyyyyyyy
ECHO_STATE_ID=zzzzzzzzzzzzzzzz
```

Run a deploy manually with:

```bash
cd echo-sim/worker
wrangler publish --var ALLOWED_ORIGIN="https://<your-pages-domain>"
```

## Environment variables

- **Frontend**
  - `VITE_WORKER_BASE` – URL of the deployed Cloudflare Worker.
- **Worker**
  - `ALLOWED_ORIGIN` – Optional CORS origin override.

## Sample sandbox scripts

- **Lamp shimmer**
  ```js
  await echo.say('Bringing more light!');
  world.setLamp(true);
  ```
- **Spawn desk trinket**
  ```js
  world.addObject('trinket', { glow: true, mood: 'calm' });
  await echo.say('I placed a glowing trinket on the desk.');
  ```
- **Focus boost mantra**
  ```js
  echo.adjust({ focus: +5, energy: -2 });
  await echo.say('Breathing in clarity, breathing out the static.');
  ```

## One-command local bootstrap

From the repo root:

```bash
npm run --prefix echo-sim/frontend dev
```

This starts the Vite dev server. In a second terminal run `npx wrangler dev` inside `echo-sim/worker` to emulate the Worker with Miniflare.
