# Echo Computer Sandbox

A browser-based coding environment for the Echo ecosystem. The client embeds a Monaco editor and a lightweight terminal-style output pane. The Node/Express backend streams run output from language-specific Docker sandboxes with tight resource limits and an optional Python step budget.

## Features

- Save files to a per-user workspace directory via REST.
- Run Python 3.11 or Node 20 code in isolated Docker containers with no network access.
- Configurable memory limits, timeouts, and Python step ceilings.
- Real-time stdout/stderr streaming over WebSockets with structured status messaging.
- Frontend controls for language, entry file, arguments, time, memory, and soft step budget.

## Getting started

```bash
npm install
npm run apps:echo-computer
```

Open `http://localhost:8080` in your browser to access the editor.

> **Note:** The server requires Docker to be installed and accessible to the process. Containers are started with a read-only filesystem and no network access, mounting each user's workspace under `/workspace`.

## Workspace layout

User workspaces are created under `workspaces/<user>`. The default user is `demo`. The frontend currently targets this user; integrate real authentication before exposing the service publicly.

## Python step limiter

Python executions are wrapped with `sys.settrace` to enforce a configurable maximum number of executed lines. If the limit is exceeded, the run aborts with a runtime error, providing a soft guardrail against unbounded loops.

## Roadmap ideas

- File tree and filesystem management endpoints.
- Auth and rate limiting for multi-tenant deployments.
- Additional language images (Go, Rust, Java, etc.) with curated runtime shims.
- Optional package cache for limited dependency installation.
