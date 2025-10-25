import hashlib

from ..shared.sandbox import Sandbox
from .. import registry


@registry.task(name="workers.attestor.run", queue="attestor")
def run(spec: dict):
    sb = Sandbox("attestor")
    files = spec.get("files", {})
    sb.write_files(files)
    digests = {path: hashlib.sha256(content.encode()).hexdigest() for path, content in files.items()}
    return {"attestation": digests}
