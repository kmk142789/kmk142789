# Continuum Temporal Guardian

Continuum epochs often arrive from distributed emitters that are not perfectly
in sync. Even small clock drift can snowball into blind spots when trying to
understand how the story of a lineage unfolded. The *Temporal Guardian*
analysis enriches the existing lineage report with signal about how well each
epoch hands off to the next.

## New anomaly signals

`echo::Continuum::analyze_lineage` now tracks temporal irregularities while it
iterates through the manifests that shape an epoch chain.

* **`temporal_anomalies`** collects human readable notes for suspicious gaps or
  overlaps. Reports highlight whether an epoch started long after its parent
  ended or if it overlapped before the parent closed.
* **`continuity_score`** quantifies how many transitions obey the declared
  parent linkage. A score of `1.0` indicates every epoch pointed at the
  manifest that preceded it.
* **`tempo_consistency`** measures the fraction of transitions that occurred
  within a dynamic tolerance window. The tolerance adapts to the observed epoch
  durations (with a 1s floor) so that brief phases are not unfairly penalised.

These signals surface drift without requiring downstream consumers to replay
raw events. They complement the existing lineage break and signature checks so
operators can distinguish between trust failures and benign scheduling jitter.

## Example interpretation

When the guardian detects a large delay, the lineage report might surface an
entry such as:

```
epoch-312 gap +42000ms after epoch-311
```

That message is paired with `tempo_consistency` dropping below `1.0`.
Conversely, overlapping epochs are flagged with an "overlaps" message so teams
can verify whether double writes were intentional or the result of a mis-tuned
orchestrator.

Together, these additions ground the Continuum lineage audit in concrete
observability metrics and make it easier to decide when an epoch stream needs
human attention.
