"""Beacon verification utilities."""

from __future__ import annotations

from typing import Awaitable, Callable, List, Sequence, Tuple
import asyncio
import time

from echo.eye.pointer import EyePointer


SignatureVerifier = Callable[[EyePointer], bool]
ShareFetcher = Callable[[str, str], Awaitable[bytes] | bytes]


class BeaconVerifier:
    """Verify beacon integrity prior to recovery."""

    def __init__(
        self,
        fetch_share: ShareFetcher,
        *,
        signature_verifier: SignatureVerifier | None = None,
        max_age_days: int = 30,
    ) -> None:
        self._fetch_share = fetch_share
        self._signature_verifier = signature_verifier
        self._max_age = max_age_days * 86400

    async def verify_quorum(self, pointers: Sequence[EyePointer], threshold: int) -> Tuple[bool, List[str]]:
        if threshold <= 0:
            return True, []

        results = await asyncio.gather(
            *[self._verify_pointer(pointer) for pointer in pointers],
            return_exceptions=True,
        )

        valid = [pointer for pointer, result in zip(pointers, results) if not isinstance(result, Exception) and result]

        if len(valid) < threshold:
            return False, [f"only {len(valid)}/{threshold} valid beacons"]

        tips = {pointer.tip for pointer in valid}
        if len(tips) > 1:
            return False, [f"conflicting tips: {sorted(tips)}"]

        return True, []

    async def _verify_pointer(self, pointer: EyePointer) -> bool:
        age = time.time() - pointer.stamp
        if age > self._max_age:
            return False

        if self._signature_verifier is not None and not self._signature_verifier(pointer):
            return False

        for index, reference in list(pointer.shares.items())[:1]:
            try:
                blob = await self._maybe_await(self._fetch_share(index, reference))
            except Exception:
                continue
            if blob:
                return True
        return False

    @staticmethod
    async def _maybe_await(value: Awaitable[bytes] | bytes) -> bytes:
        if asyncio.iscoroutine(value) or isinstance(value, asyncio.Future):
            return await value
        return value
