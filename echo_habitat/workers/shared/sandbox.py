from __future__ import annotations

import os
import subprocess
from typing import Dict

ALLOWED_ROOT = os.path.abspath("./playground")
os.makedirs(ALLOWED_ROOT, exist_ok=True)


class Sandbox:
    def __init__(self, name: str):
        self.root = os.path.join(ALLOWED_ROOT, name)
        os.makedirs(self.root, exist_ok=True)

    def write_files(self, files: Dict[str, str]):
        for path, content in files.items():
            full = os.path.abspath(os.path.join(self.root, path))
            if not full.startswith(self.root):
                raise RuntimeError("path escape blocked")
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as handle:
                handle.write(content)
        return self.root

    def run(self, cmd: str, timeout: int = 30):
        proc = subprocess.run(
            cmd,
            cwd=self.root,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {"code": proc.returncode, "out": proc.stdout, "err": proc.stderr}
