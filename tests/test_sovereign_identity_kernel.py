from datetime import datetime, timedelta, timezone
from pathlib import Path

from echo.sovereign_identity_kernel import (
    CapabilityIdentityKernel,
    IdentityKernelConfig,
)


def test_capability_identity_kernel_roundtrip(tmp_path: Path) -> None:
    shell_path = tmp_path / "echo_shell.py"
    shell_path.write_text("print('ok')\n", encoding="utf-8")
    artifact_path = tmp_path / "upgrade.bin"
    artifact_path.write_text("upgrade", encoding="utf-8")

    config = IdentityKernelConfig(vault_root=tmp_path / "vault", passphrase="pass", shell_path=shell_path)
    kernel = CapabilityIdentityKernel(config)

    claims = {"did": kernel.issuer_did, "role": "guardian", "jurisdiction": "GLB"}
    proof = kernel.selective_disclosure(claims, reveal=["did", "role"])
    assert proof.disclosed["did"] == kernel.issuer_did
    assert proof.verify(claims=claims)

    expires = datetime.now(timezone.utc) + timedelta(days=1)
    credential = kernel.issue_capability(
        subject_did="did:echo:agent:alpha",
        capabilities=["macro.orchestrate"],
        expires_at=expires,
    )
    assert credential.issuer == kernel.issuer_did
    assert credential.capabilities == ["macro.orchestrate"]

    node = kernel.record_shell_integrity()
    assert node.statement == "echoshell-integrity"

    upgrade = kernel.self_attest_upgrade(
        component="macro",
        description="stability-upgrade",
        artifact_path=artifact_path,
    )
    assert upgrade.component == "macro"

    envelope = kernel.encode_command("reboot", hint="ops")
    assert kernel.decode_command(envelope) == "reboot"

    snapshot = kernel.snapshot()
    assert snapshot.issuer_did == kernel.issuer_did
    assert snapshot.shared_command_secret
    assert snapshot.identity_state["proof_pipeline"]["depth"] >= 3
    assert snapshot.identity_state["capabilities"]
