"""Project-wide Python site customisation for tests and scripts.

This repository keeps most of the reusable source code under
``packages/core/src`` so that it can be published as part of a namespace
package.  The unit tests in this kata import the legacy top-level modules
such as :mod:`echo_evolver` directly.  When the project is checked out
without installing the package, those imports would fail because the
``packages/core/src`` directory is not on :data:`sys.path` by default.

To keep the source tree importable without requiring installation we add
the directory to :data:`sys.path` at interpreter start-up.  Python loads
``sitecustomize`` automatically after the standard site initialisation,
which makes it a convenient place to apply this adjustment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Resolve the repository root from this file and compute the location of the
# core package sources.  Using ``resolve()`` normalises any symbolic links so
# the same path isn't inserted multiple times under different spellings.
PROJECT_ROOT = Path(__file__).resolve().parent
CORE_SRC = PROJECT_ROOT / "packages" / "core" / "src"

# ``sys.path`` can contain duplicate entries; inserting only when necessary
# avoids growing the list each time a test process starts.  We also ensure the
# path is added near the front so that imports prefer the in-tree sources over
# any globally installed versions.
core_str = os.fspath(CORE_SRC)
if core_str not in sys.path:
    sys.path.insert(0, core_str)
