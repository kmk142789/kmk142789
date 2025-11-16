# Autonomous Continuous Task Governance

Echo's `autonomousSystemAccess` surface now exposes richer continuous-task health monitoring so stewards can see when background rituals have fallen behind cadence and optionally pause them automatically.

## API additions

### `GET /echo/system/task/report`
* Query params:
  * `warningMultiplier` (optional number) – number of cadences that must elapse before a task is marked `warning`.
  * `criticalMultiplier` (optional number) – number of cadences that must elapse before a task is marked `critical`.
  * `includeHistory=true` to embed the bounded event log for each task.
* Response: `{ report: { summary, tasks, assessedAt } }` where each task contains its serialized state plus a `health` object with `state`, `severity`, `overdueMs`, and `missedHeartbeats`.

### `POST /echo/system/task/autogovern`
* Body params:
  * `warningMultiplier`, `criticalMultiplier` – forwarded to the underlying health engine.
  * `autoStopMultiplier` – number of cadences without a heartbeat required before Echo auto-pauses the task.
  * `includeHistory` – boolean flag for embedding history in the nested assessment payload.
* Response: `{ report: { summary, actions, assessment } }`. When a task breaches the `autoStopMultiplier` threshold Echo records an `auto-govern` history event and marks the task status `auto-paused` with a `stopReason` of `auto-governed: missed heartbeat window`.

## Task serialization updates

`lib/autonomous_system_access.js` now annotates every task serialization with a `health` object even when using the existing endpoints. Client dashboards can surface the drift, missed heartbeat count, and severity without recomputing those metrics.
