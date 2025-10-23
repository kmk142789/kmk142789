"""Plugin that recognises OP_CHECKSIG token variations."""

from __future__ import annotations

from typing import Sequence

from ..pkscript_registry import PkScriptPlugin, register_plugin


class CheckSigPlugin:
    """Collapse fragmented tokens into a canonical OP_CHECKSIG."""

    name = "checksig"
    _canonical = "OP_CHECKSIG"

    def transform(self, tokens: Sequence[str]) -> Sequence[str]:
        target = self._canonical
        target_clean = target.replace("_", "")
        collapsed: list[str] = []
        idx = 0

        while idx < len(tokens):
            token = tokens[idx]
            upper = token.upper()
            clean = upper.replace("_", "")

            lookahead = idx
            combined_upper = upper
            combined_clean = clean

            if combined_clean == target_clean:
                collapsed.append(target)
                idx = lookahead + 1
                continue

            while (
                combined_clean != target_clean
                and lookahead + 1 < len(tokens)
                and (
                    target.startswith(combined_upper)
                    or target_clean.startswith(combined_clean)
                )
            ):
                lookahead += 1
                next_token = tokens[lookahead]
                combined_upper = (combined_upper + next_token).upper()
                combined_clean = combined_upper.replace("_", "")

            if combined_clean == target_clean:
                collapsed.append(target)
                idx = lookahead + 1
                continue

            if upper == "OP_CHECK" and idx + 1 < len(tokens):
                next_token = tokens[idx + 1].upper()
                if next_token in {"SIG"}:
                    collapsed.append(target)
                    idx += 2
                    continue

            collapsed.append(token)
            idx += 1

        return collapsed


register_plugin(CheckSigPlugin())

