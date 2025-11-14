"""Brute-force scanner for legacy Bitcoin puzzle addresses.

This script modernises the classic Mizogg-style random search loop by wiring it
into the repository's structured puzzle index, exposing CLI parameters, and
adding optional multiprocessing along with JSONL logging for hits.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import secrets
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple

# --- secp256k1 parameters ----------------------------------------------------

_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


@dataclass(frozen=True)
class _Point:
    """Affine point on the secp256k1 curve."""

    x: Optional[int]
    y: Optional[int]

    @property
    def is_infinity(self) -> bool:
        return self.x is None or self.y is None


_INFINITY = _Point(None, None)
_GENERATOR = _Point(_GX, _GY)
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass(frozen=True)
class CandidateMatch:
    """Successful candidate emitted by the scanner."""

    private_key: int
    private_key_hex: str
    address_type: str
    address: str
    wif: str
    hash160: str


@dataclass(frozen=True)
class ScanConfig:
    minimum: int
    maximum: int
    iterations: int
    progress_interval: int
    stop_on_hit: bool
    worker_id: int = 0


def _inverse_mod(k: int, p: int = _P) -> int:
    if k % p == 0:
        raise ZeroDivisionError("inverse does not exist")
    return pow(k, p - 2, p)


def _point_add(p1: _Point, p2: _Point) -> _Point:
    if p1.is_infinity:
        return p2
    if p2.is_infinity:
        return p1

    if p1.x == p2.x and (p1.y != p2.y or p1.y == 0):
        return _INFINITY

    if p1 == p2:
        m = (3 * p1.x * p1.x) * _inverse_mod(2 * p1.y, _P)
    else:
        m = (p2.y - p1.y) * _inverse_mod((p2.x - p1.x) % _P, _P)

    m %= _P
    x3 = (m * m - p1.x - p2.x) % _P
    y3 = (m * (p1.x - x3) - p1.y) % _P
    return _Point(x3, y3)


def _scalar_multiply(k: int, point: _Point = _GENERATOR) -> _Point:
    if k % _N == 0 or point.is_infinity:
        return _INFINITY

    result = _INFINITY
    addend = point
    remaining = k

    while remaining:
        if remaining & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        remaining >>= 1

    return result


def _hash160(data: bytes) -> bytes:
    import hashlib

    sha = hashlib.sha256(data).digest()
    ripemd = hashlib.new("ripemd160", sha).digest()
    return ripemd


def _base58check_encode(payload: bytes) -> str:
    import hashlib

    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    full_payload = payload + checksum

    number = int.from_bytes(full_payload, "big")
    encoded = ""
    while number:
        number, remainder = divmod(number, 58)
        encoded = _BASE58_ALPHABET[remainder] + encoded

    leading_zero_bytes = len(full_payload) - len(full_payload.lstrip(b"\x00"))
    return "1" * leading_zero_bytes + (encoded or "1")


def private_key_to_wif(value: int, compressed: bool) -> str:
    payload = value.to_bytes(32, "big")
    versioned = b"\x80" + payload + (b"\x01" if compressed else b"")
    return _base58check_encode(versioned)


def public_keys_from_private(private_key: int) -> Tuple[bytes, bytes]:
    if not 1 <= private_key < _N:
        raise ValueError("private key out of secp256k1 range")

    point = _scalar_multiply(private_key)
    if point.is_infinity or point.x is None or point.y is None:
        raise ValueError("failed to derive public key")

    x_bytes = point.x.to_bytes(32, "big")
    y_bytes = point.y.to_bytes(32, "big")

    prefix = b"\x02" if point.y % 2 == 0 else b"\x03"
    compressed = prefix + x_bytes
    uncompressed = b"\x04" + x_bytes + y_bytes
    return compressed, uncompressed


def p2pkh_address(pubkey: bytes) -> str:
    payload = b"\x00" + _hash160(pubkey)
    return _base58check_encode(payload)


def load_targets(index_path: Path, extra_targets: Optional[Path]) -> Tuple[Set[str], Set[str]]:
    with index_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    addresses: Set[str] = set()
    hashes: Set[str] = set()
    for entry in payload.get("puzzles", []):
        address = entry.get("address")
        if isinstance(address, str) and address.strip():
            addresses.add(address.strip())
        h160 = entry.get("hash160")
        if isinstance(h160, str) and len(h160.strip()) == 40:
            hashes.add(h160.strip().lower())

    if extra_targets:
        for raw in extra_targets.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if len(line) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in line):
                hashes.add(line.lower())
            else:
                addresses.add(line)

    return addresses, hashes


def evaluate_candidate(private_key: int, addresses: Set[str], hashes: Set[str]) -> List[CandidateMatch]:
    matches: List[CandidateMatch] = []
    compressed_key, uncompressed_key = public_keys_from_private(private_key)

    for addr_type, pubkey, compressed in (
        ("compressed", compressed_key, True),
        ("uncompressed", uncompressed_key, False),
    ):
        fingerprint_bytes = _hash160(pubkey)
        address = _base58check_encode(b"\x00" + fingerprint_bytes)
        fingerprint = fingerprint_bytes.hex()
        if address in addresses or fingerprint in hashes:
            matches.append(
                CandidateMatch(
                    private_key=private_key,
                    private_key_hex=f"{private_key:064x}",
                    address_type=addr_type,
                    address=address,
                    wif=private_key_to_wif(private_key, compressed=compressed),
                    hash160=fingerprint,
                )
            )

    return matches


def _write_matches(path: Optional[Path], matches: Sequence[CandidateMatch]) -> None:
    if not path or not matches:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for match in matches:
            json.dump(match.__dict__, handle)
            handle.write("\n")


def _worker(config: ScanConfig, addresses: Set[str], hashes: Set[str], output: Optional[Path], lock: Optional[mp.Lock], stop: Optional[mp.Event]) -> None:
    rng = secrets.SystemRandom()
    attempts = 0
    start = time.perf_counter()

    def log(message: str) -> None:
        prefix = f"[worker {config.worker_id}] "
        text = prefix + message
        if lock:
            with lock:
                print(text)
        else:
            print(text)

    while (config.iterations == 0 or attempts < config.iterations) and (stop is None or not stop.is_set()):
        candidate = rng.randrange(config.minimum, config.maximum + 1)
        matches = evaluate_candidate(candidate, addresses, hashes)
        if matches:
            log(
                "hit after %d attempts in %.1fs (%s)"
                % (
                    attempts + 1,
                    time.perf_counter() - start,
                    ", ".join(match.address for match in matches),
                )
            )
            _write_matches(output, matches)
            for match in matches:
                log(
                    f"{match.address_type} match: key={match.private_key_hex} wif={match.wif} address={match.address}"
                )
            if config.stop_on_hit and stop is not None:
                stop.set()
                return
        attempts += 1
        if config.progress_interval and attempts % config.progress_interval == 0:
            elapsed = time.perf_counter() - start
            log(f"scanned {attempts} candidates in {elapsed:.1f}s without a hit")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--minimum",
        type=int,
        default=1,
        help="Lower inclusive bound for the private key search space.",
    )
    parser.add_argument(
        "--maximum",
        type=int,
        default=_N - 1,
        help="Upper inclusive bound for the private key search space.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Number of random candidates to test per worker (0 = infinite).",
    )
    parser.add_argument(
        "--progress",
        type=int,
        default=5000,
        help="Print a progress message every N attempts per worker.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes to spawn.",
    )
    parser.add_argument(
        "--stop-on-hit",
        action="store_true",
        help="Signal all workers to stop after the first hit is recorded.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSONL output file for recording hits.",
    )
    parser.add_argument(
        "--puzzle-index",
        type=Path,
        default=Path("data/puzzle_index.json"),
        help="Path to the shared puzzle index JSON file.",
    )
    parser.add_argument(
        "--extra-targets",
        type=Path,
        help="Optional newline-delimited file of addresses or hash160 fingerprints to monitor.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.minimum < 1:
        print("[error] minimum must be >= 1", file=sys.stderr)
        return 1
    if args.maximum >= _N:
        print("[error] maximum must be less than the secp256k1 order", file=sys.stderr)
        return 1
    if args.minimum >= args.maximum:
        print("[error] minimum must be less than maximum", file=sys.stderr)
        return 1

    addresses, hashes = load_targets(args.puzzle_index, args.extra_targets)
    if not addresses and not hashes:
        print("[error] no targets were loaded", file=sys.stderr)
        return 1

    print(f"Loaded {len(addresses)} addresses and {len(hashes)} hash160 fingerprints.")
    print(
        f"Scanning range [{args.minimum}, {args.maximum}] using {args.workers} worker(s); iterations per worker: {args.iterations or 'infinite'}."
    )

    config = ScanConfig(
        minimum=args.minimum,
        maximum=args.maximum,
        iterations=args.iterations,
        progress_interval=args.progress,
        stop_on_hit=args.stop_on_hit,
    )

    if args.workers <= 1:
        _worker(config, addresses, hashes, args.output, None, None)
        return 0

    ctx = mp.get_context("spawn")
    lock = ctx.Lock()
    stop_event = ctx.Event() if args.stop_on_hit else None
    processes: List[mp.Process] = []
    for worker_id in range(args.workers):
        worker_config = ScanConfig(
            minimum=config.minimum,
            maximum=config.maximum,
            iterations=config.iterations,
            progress_interval=config.progress_interval,
            stop_on_hit=config.stop_on_hit,
            worker_id=worker_id,
        )
        process = ctx.Process(
            target=_worker,
            args=(worker_config, addresses, hashes, args.output, lock, stop_event),
        )
        process.start()
        processes.append(process)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("[main] Keyboard interrupt received, terminating workers...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
