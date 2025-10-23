"""Plugin that recognises OP_CHECKSIG token variations."""

from __future__ import annotations

from typing import Sequence

from ..pkscript_registry import PkScriptPlugin, register_plugin


class CheckSigPlugin:
    """Collapse fragmented tokens into a canonical OP_CHECKSIG."""

    name = "checksig"
    _canonical = "OP_CHECKSIG"

    @staticmethod
    def _normalise(token: str) -> str:
        """Return ``token`` uppercased with separators removed."""

        return token.upper().replace("_", "").replace("-", "")

    def transform(self, tokens: Sequence[str]) -> Sequence[str]:
        target = self._canonical
        target_clean = self._normalise(target)
        collapsed: list[str] = []
        idx = 0

        while idx < len(tokens):
            token = tokens[idx]
            upper = token.upper()
            clean = self._normalise(token)

            lookahead = idx
            combined_clean = clean

            if combined_clean == target_clean:
                collapsed.append(target)
                idx = lookahead + 1
                continue

            while (
                combined_clean != target_clean
                and lookahead + 1 < len(tokens)
                and target_clean.startswith(combined_clean)
            ):
                lookahead += 1
                next_token = tokens[lookahead]
                combined_clean += self._normalise(next_token)

            if combined_clean == target_clean:
                collapsed.append(target)
                idx = lookahead + 1
                continue

            if (
                clean == self._normalise("OP_CHECK")
                and idx + 1 < len(tokens)
                and self._normalise(tokens[idx + 1]) == self._normalise("SIG")
            ):
                collapsed.append(target)
                idx += 2
                continue

            collapsed.append(token)
            idx += 1

        return collapsed


register_plugin(CheckSigPlugin())

