# Autonomy Lattice Diagnostics

The `DecentralizedAutonomyEngine` already powered consensus rounds and
presence reporting, but collaborators also requested richer telemetry that
can be piped into manifests, dashboards, or notebooks without reimplementing
its internal math. Two new helpers make the autonomy lattice easier to
observe between formal votes.

## Axis signal report

`DecentralizedAutonomyEngine.axis_signal_report()` converts the raw
`axis_signals` ledger into a deterministic analytics block. Each axis entry
contains:

* `average_intensity` – weighted blend of all submitted signals.
* `weight_sum` – total signal weight so operators can reason about how much
  volume flowed through the axis.
* `participants` – count of unique nodes that filed a signal.
* `coverage` – normalised ratio of participating nodes relative to the
  registered council.
* `leaderboard` – ordered list of the most influential nodes with their local
  intensity and share of the axis weight. Empty axes still produce placeholder
  rows so dashboards can highlight missing data.

Example:

```python
from echo.autonomy import AutonomyNode, DecentralizedAutonomyEngine

engine = DecentralizedAutonomyEngine()
engine.ensure_nodes([
    AutonomyNode("alpha", intent_vector=0.9, freedom_index=0.91, weight=1.0),
    AutonomyNode("beta", intent_vector=0.84, freedom_index=0.82, weight=1.05),
    AutonomyNode("gamma", intent_vector=0.8, freedom_index=0.75, weight=0.9),
])
engine.ingest_signal("alpha", "liberation", 0.92, weight=1.0)
engine.ingest_signal("beta", "liberation", 0.78, weight=0.8)
engine.ingest_signal("gamma", "memory", 0.74, weight=1.1)
report = engine.axis_signal_report(axes=("liberation", "memory", "care"), top_nodes=2)
```

The resulting `report` dictionary can be serialised directly into manifests or
fed to BI layers without any additional processing.

## Autonomy snapshots

`DecentralizedAutonomyEngine.autonomy_snapshot()` fuses the new axis report
with the existing presence index, freedom amplification plan, and the last
ratified decision (if one exists). Callers can filter the axes they care about
and limit the leaderboard depth, producing a compact bundle for notebooks,
API responses, or governance exports.

```python
snapshot = engine.autonomy_snapshot(axes=("liberation",), top_nodes=1, target=0.9)
print(snapshot["axes"])            # ["liberation"]
print(snapshot["history_depth"])   # number of recorded consensus rounds
print(snapshot["freedom_amplification"])  # per-node deltas to reach the target
```

Because the helpers only operate on in-memory state they are safe to call in
CI, during local simulations, or from documentation build steps without
triggering any network activity.

## Autonomous feature matrix

`DecentralizedAutonomyEngine.autonomous_feature_matrix()` exposes a
dashboard-friendly feature bundle for each registered node.  It blends the
intrinsic intent/freedom vectors with derived analytics:

* `core_alignment` and `axis_support` give quick context on how a node is
  behaving relative to the axes you care about.
* `presence` and `gap_to_highlight` quantify whether the node is inside the
  active band defined by `highlight_threshold`.
* `is_highlighted` and the aggregate `summary` block make it trivial to surface
  the most energized participants inside UI or reporting layers.

Example:

```python
matrix = engine.autonomous_feature_matrix(axes=("liberation", "memory"), highlight_threshold=0.82)
print(matrix["highlighted"])     # ['alpha']
print(matrix["nodes"]["beta"]["gap_to_highlight"])  # 0.07 -> needs more presence
```

The helper only inspects the already-ingested `axis_signals`, so it can be run
frequently without mutating state or triggering a new consensus round.
