from pathlib import Path
import json

from ledger.sovereign_ledger_layer import (
    AutonomousFeatureUpgradeRecord,
    SovereignLedgerLayer,
)


def _layer(tmp_path: Path) -> SovereignLedgerLayer:
    return SovereignLedgerLayer(
        registry_path=tmp_path / "registry.jsonl",
        credential_dir=tmp_path / "creds",
        feature_registry_path=tmp_path / "features.jsonl",
        feature_upgrade_registry_path=tmp_path / "feature_upgrades.jsonl",
    )


def test_record_autonomous_feature_upgrade(tmp_path: Path) -> None:
    layer = _layer(tmp_path)
    feature_artifact = tmp_path / "feature.json"
    feature_artifact.write_text("v1 feature", encoding="utf-8")

    feature = layer.record_autonomous_feature(
        codename="Echo Bridge Constellation Autopilot",
        amendment_reference="Amendment III",
        objective="Sync bridges",
        success_criteria=["bridges aligned"],
        ledger_anchor="echo-sovereign-ledger:feature:bridge-constellation",
        artifact_path=feature_artifact,
    )

    upgraded_artifact = tmp_path / "feature_v2.json"
    upgraded_artifact.write_text("v2 feature", encoding="utf-8")

    upgrade = layer.record_autonomous_feature_upgrade(
        base_feature_id=feature.feature_id,
        codename=feature.codename,
        reason="Expanded bridge matrix",
        ledger_anchor="echo-sovereign-ledger:feature:bridge-constellation-upgrade",
        artifact_path=upgraded_artifact,
    )

    assert isinstance(upgrade, AutonomousFeatureUpgradeRecord)
    assert upgrade.from_feature_id == feature.feature_id
    assert upgrade.to_feature_id.startswith("feature:")
    assert (tmp_path / "feature_upgrades.jsonl").exists()

    recorded = json.loads((tmp_path / "feature_upgrades.jsonl").read_text(encoding="utf-8"))
    assert recorded["upgrade_id"].startswith("feature-upgrade:")
    assert recorded["codename"] == feature.codename


def test_load_autonomous_features(tmp_path: Path) -> None:
    layer = _layer(tmp_path)
    artifact = tmp_path / "feature.json"
    artifact.write_text("content", encoding="utf-8")

    record = layer.record_autonomous_feature(
        codename="Bridge Trust Graph Orchestrator",
        amendment_reference="Amendment IV",
        objective="Activate trust graph",
        success_criteria=["publish credentials"],
        ledger_anchor="echo-sovereign-ledger:feature:bridge-trust-graph",
        artifact_path=artifact,
    )

    features = layer.load_autonomous_features()
    assert len(features) == 1
    assert features[0].feature_id == record.feature_id
