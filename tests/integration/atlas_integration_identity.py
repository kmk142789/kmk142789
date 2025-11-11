import asyncio
from pathlib import Path

from atlas.identity import CredentialIssuer, CredentialVerifier, DIDCache, DIDResolver, RotatingKeyManager


def test_issue_and_verify(tmp_path: Path):
    manager = RotatingKeyManager.generate()
    seed, _ = manager.derive()
    issuer = CredentialIssuer.from_seed(seed, "did:example:issuer")
    credential = issuer.issue("did:example:holder", {"role": "tester"})
    verifier = CredentialVerifier.from_bytes(issuer.export_public_key())
    assert verifier.verify(credential)


def test_did_cache(tmp_path: Path):
    async def run() -> None:
        cache = DIDCache(tmp_path / "cache.json")
        resolver = DIDResolver(cache, endpoint="https://example.com/did")
        cache.set("did:example:one", {"id": "did:example:one"})
        doc = await resolver.resolve("did:example:one")
        assert doc["id"] == "did:example:one"

    asyncio.run(run())
