"""Cross-chain script decoding utilities.

This module exposes a minimal registry-driven interface for decoding
transaction scripts and calldata across multiple blockchain ecosystems.
Each decoder produces a :class:`ScriptDecodingResult` that contains a
normalised set of attributes regardless of the originating chain.  The
metadata payload can be extended with chain specific hints without
breaking callers that only care about the common structure.

The initial implementation ships with decoders for Bitcoin, Ethereum and
Solana.  New chains can be added by implementing
``ScriptDecoder.decode`` and registering the instance with the global
``registry``.
"""

from __future__ import annotations

import base64
import json
import string
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence


class ScriptDecodingError(ValueError):
    """Raised when a decoder cannot interpret the supplied script."""


@dataclass(slots=True)
class ScriptDecodingResult:
    """Normalised representation of a decoded script."""

    chain: str
    addresses: List[str]
    opcode_trace: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON serialisable representation of the result."""

        return {
            "chain": self.chain,
            "addresses": list(self.addresses),
            "opcode_trace": list(self.opcode_trace),
            "metadata": dict(self.metadata),
        }


class ScriptDecoder:
    """Base class for chain specific script decoders."""

    chain: str

    def decode(self, script: Any, **kwargs: Any) -> ScriptDecodingResult:  # pragma: no cover - virtual
        raise NotImplementedError


class ScriptDecoderRegistry:
    """Simple registry used to look up decoders by chain name."""

    def __init__(self) -> None:
        self._decoders: Dict[str, ScriptDecoder] = {}

    def register(self, decoder: ScriptDecoder) -> None:
        key = decoder.chain.lower()
        self._decoders[key] = decoder

    def get(self, chain: str) -> ScriptDecoder:
        try:
            return self._decoders[chain.lower()]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ScriptDecodingError(f"unknown chain '{chain}'") from exc

    def chains(self) -> List[str]:
        return sorted(self._decoders.keys())

    def decode(self, chain: str, script: Any, **kwargs: Any) -> ScriptDecodingResult:
        decoder = self.get(chain)
        return decoder.decode(script, **kwargs)


registry = ScriptDecoderRegistry()


# -- Bitcoin -----------------------------------------------------------------

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_GENERATORS = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


class PkScriptError(ScriptDecodingError):
    """Raised when a Bitcoin script cannot be interpreted."""


def _looks_like_base58(value: str) -> bool:
    if not value:
        return False
    cleaned = value.replace("-", "")
    if not cleaned:
        return False
    try:
        candidate = cleaned.encode("ascii")
    except UnicodeEncodeError:
        return False
    return all(chr(byte) in _BASE58_ALPHABET for byte in candidate)


def _base58_encode(data: bytes) -> str:
    number = int.from_bytes(data, "big")
    result = ""
    while number > 0:
        number, mod = divmod(number, 58)
        result = _BASE58_ALPHABET[mod] + result
    leading_zeroes = 0
    for byte in data:
        if byte == 0:
            leading_zeroes += 1
        else:
            break
    return "1" * leading_zeroes + result


def _base58check_encode(version: int, payload: bytes) -> str:
    if not 0 <= version <= 0xFF:
        raise ValueError("version must fit inside a single byte")
    data = bytes([version]) + payload
    checksum = BitcoinScriptDecoder.hash256(data)[:4]
    return _base58_encode(data + checksum)


def _normalise_lines(lines: Iterable[str]) -> List[str]:
    return [line.strip() for line in lines if line.strip()]


def _collapse_op_checksig(sequence: List[str]) -> List[str]:
    target = "OP_CHECKSIG"
    target_clean = target.replace("_", "")
    collapsed: List[str] = []
    idx = 0
    while idx < len(sequence):
        token = sequence[idx]
        upper = token.upper()
        clean = upper.replace("_", "")

        if target.startswith(upper) or target_clean.startswith(clean):
            combined_upper = upper
            combined_clean = clean
            lookahead = idx

            while (
                combined_clean != target_clean
                and lookahead + 1 < len(sequence)
                and (
                    target.startswith(combined_upper)
                    or target_clean.startswith(combined_clean)
                )
            ):
                lookahead += 1
                next_token = sequence[lookahead]
                combined_upper = (combined_upper + next_token).upper()
                combined_clean = combined_upper.replace("_", "")

            if combined_clean == target_clean:
                collapsed.append(target)
                idx = lookahead + 1
                continue

        if upper == "OP_CHECK" and idx + 1 < len(sequence):
            next_token = sequence[idx + 1].upper()
            if next_token in {"SIG"}:
                collapsed.append(target)
                idx += 2
                continue

        collapsed.append(token)
        idx += 1
    return collapsed


def _convertbits(data: bytes, from_bits: int, to_bits: int, *, pad: bool = True) -> List[int]:
    acc = 0
    bits = 0
    result: List[int] = []
    max_value = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1

    for value in data:
        if value < 0 or value >> from_bits:
            raise ValueError("invalid value for convertbits")
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits

        while bits >= to_bits:
            bits -= to_bits
            result.append((acc >> bits) & max_value)

    if pad:
        if bits:
            result.append((acc << (to_bits - bits)) & max_value)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & max_value):
        raise ValueError("invalid padding in convertbits")

    return result


def _bech32_polymod(values: Iterable[int]) -> int:
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for idx, generator in enumerate(_BECH32_GENERATORS):
            if (top >> idx) & 1:
                chk ^= generator
    return chk


def _bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(ch) >> 5 for ch in hrp] + [0] + [ord(ch) & 31 for ch in hrp]


def _create_bech32_checksum(hrp: str, data: Iterable[int], const: int) -> List[int]:
    values = _bech32_hrp_expand(hrp) + list(data)
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - idx)) & 31 for idx in range(6)]


def _bech32_encode(hrp: str, data: Iterable[int], *, spec: str = "bech32") -> str:
    const = 1 if spec == "bech32" else 0x2BC830A3
    combined = list(data) + _create_bech32_checksum(hrp, data, const)
    return hrp + "1" + "".join(_BECH32_ALPHABET[d] for d in combined)


def _is_hex_string(value: str) -> bool:
    return bool(value) and all(char in string.hexdigits for char in value)


def _collect_hex_tokens(tokens: List[str]) -> tuple[str, int]:
    collected: List[str] = []
    for token in tokens:
        if _is_hex_string(token):
            collected.append(token)
        else:
            break
    return "".join(collected), len(collected)


class BitcoinScriptDecoder(ScriptDecoder):
    chain = "bitcoin"

    @staticmethod
    def hash256(data: bytes) -> bytes:
        import hashlib

        return hashlib.sha256(hashlib.sha256(data).digest()).digest()

    @staticmethod
    def hash160(data: bytes) -> bytes:
        import hashlib

        sha = hashlib.sha256(data).digest()
        return hashlib.new("ripemd160", sha).digest()

    def _normalise_input(self, script: Any) -> List[str]:
        if isinstance(script, (list, tuple)):
            lines = [str(token) for token in script]
        elif isinstance(script, str):
            if script.strip().startswith("[") and script.strip().endswith("]"):
                try:
                    parsed = json.loads(script)
                except json.JSONDecodeError:
                    lines = script.splitlines()
                else:
                    if isinstance(parsed, list):
                        lines = [str(token) for token in parsed]
                    else:
                        raise PkScriptError("JSON script representation must be a list")
            else:
                lines = script.splitlines()
        else:
            raise PkScriptError("unsupported script input type")

        flattened: List[str] = []
        for entry in lines:
            if isinstance(entry, str):
                parts = entry.replace(":", " ").replace(",", " ").split()
                flattened.extend(parts)
            else:
                flattened.append(str(entry))
        return flattened

    def _pkscript_to_hash(
        self, tokens: Sequence[str]
    ) -> tuple[str, str, Optional[int], List[str]]:
        sequence = _collapse_op_checksig([token.strip() for token in tokens if token.strip()])

        if sequence and _looks_like_base58(sequence[0]):
            sequence = sequence[1:]

        if sequence and sequence[0].lower() == "pkscript":
            sequence = sequence[1:]

        normalised_trace = list(sequence)

        expected = [
            "OP_DUP",
            "OP_HASH160",
            "OP_EQUALVERIFY",
            "OP_CHECKSIG",
        ]

        if (
            len(sequence) == 5
            and sequence[0:2] == expected[:2]
            and sequence[3:] == expected[2:]
        ):
            hash_candidate = sequence[2]

            if len(hash_candidate) != 40:
                raise PkScriptError("pubkey hash must be 20 bytes of hex")

            try:
                bytes.fromhex(hash_candidate)
            except ValueError as exc:
                raise PkScriptError("pubkey hash must be hexadecimal") from exc

            return "p2pkh", hash_candidate, None, normalised_trace

        if len(sequence) == 2 and sequence[1].upper() == "OP_CHECKSIG":
            pubkey_hex = sequence[0]
            try:
                pubkey_bytes = bytes.fromhex(pubkey_hex)
            except ValueError as exc:
                raise PkScriptError("public key must be hexadecimal") from exc

            if len(pubkey_bytes) not in {33, 65}:
                raise PkScriptError("public key must be 33 or 65 bytes long")

            if len(pubkey_bytes) == 33 and pubkey_bytes[0] not in (0x02, 0x03):
                raise PkScriptError("compressed public key must start with 0x02 or 0x03")

            if len(pubkey_bytes) == 65 and pubkey_bytes[0] != 0x04:
                raise PkScriptError("uncompressed public key must start with 0x04")

            return "p2pkh", self.hash160(pubkey_bytes).hex(), None, normalised_trace

        if (
            len(sequence) == 3
            and sequence[0].upper() == "OP_HASH160"
            and sequence[2].upper() == "OP_EQUAL"
        ):
            hash_candidate = sequence[1]

            if len(hash_candidate) != 40:
                raise PkScriptError("script hash must be 20 bytes of hex")

            try:
                bytes.fromhex(hash_candidate)
            except ValueError as exc:
                raise PkScriptError("script hash must be hexadecimal") from exc

            return "p2sh", hash_candidate, None, normalised_trace

        if sequence:
            version_token = sequence[0].upper()
            witness_version: Optional[int]
            if version_token in {"OP_0", "0"}:
                witness_version = 0
            elif version_token.startswith("OP_") and version_token[3:].isdigit():
                witness_version = int(version_token[3:])
                if not (1 <= witness_version <= 16):
                    witness_version = None
            else:
                witness_version = None

            if witness_version is not None:
                program_hex, consumed = _collect_hex_tokens(sequence[1:])

                if not program_hex:
                    raise PkScriptError("witness program must follow the version opcode")

                if consumed != len(sequence) - 1:
                    raise PkScriptError("unexpected tokens after witness program")

                if len(program_hex) % 2 != 0:
                    raise PkScriptError("witness program must be an even number of hex digits")

                try:
                    program = bytes.fromhex(program_hex)
                except ValueError as exc:
                    raise PkScriptError("witness program must be hexadecimal") from exc

                if len(program) == 20:
                    return "p2wpkh", program_hex, witness_version, normalised_trace
                if len(program) == 32:
                    script_kind = "p2tr" if witness_version == 1 else "p2wsh"
                    return script_kind, program_hex, witness_version, normalised_trace

                raise PkScriptError("unsupported witness program length for address conversion")

        raise PkScriptError("unsupported script layout for address conversion")

    def decode(self, script: Any, **kwargs: Any) -> ScriptDecodingResult:
        network = kwargs.get("network", "mainnet")
        hrp_override = kwargs.get("hrp")

        tokens = self._normalise_input(script)
        script_type, hash_hex, witness_version, trace = self._pkscript_to_hash(tokens)

        version_map: Dict[str, MutableMapping[str, Any]] = {
            "mainnet": {"p2pkh": 0x00, "p2sh": 0x05, "bech32_hrp": "bc"},
            "testnet": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "tb"},
            "regtest": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "bcrt"},
        }

        try:
            script_versions = version_map[network.lower()]
        except KeyError as exc:
            raise ScriptDecodingError(f"unknown Bitcoin network '{network}'") from exc

        address: Optional[str] = None
        metadata: Dict[str, Any] = {
            "script_type": script_type,
            "network": network,
            "payload_hex": hash_hex,
        }

        if witness_version is not None:
            metadata["witness_version"] = witness_version

        if script_type in {"p2pkh", "p2sh"}:
            version = script_versions[script_type]
            address = _base58check_encode(version, bytes.fromhex(hash_hex))
        elif script_type in {"p2wpkh", "p2wsh", "p2tr"}:
            hrp = hrp_override or script_versions.get("bech32_hrp")
            if not isinstance(hrp, str):  # pragma: no cover - defensive guard
                raise PkScriptError("network does not define a bech32 HRP")
            if witness_version is None:  # pragma: no cover - defensive guard
                raise PkScriptError("missing witness version for segwit script")
            program = bytes.fromhex(hash_hex)
            words = _convertbits(program, 8, 5, pad=True)
            spec = "bech32" if witness_version == 0 else "bech32m"
            address = _bech32_encode(hrp, [witness_version] + words, spec=spec)
            metadata["bech32_hrp"] = hrp
        else:
            raise PkScriptError(f"unsupported script type '{script_type}'")

        return ScriptDecodingResult(
            chain=self.chain,
            addresses=[address] if address else [],
            opcode_trace=trace,
            metadata=metadata,
        )


# -- Ethereum ----------------------------------------------------------------


class EthereumScriptDecoder(ScriptDecoder):
    chain = "ethereum"

    def __init__(self) -> None:
        self._opcodes = self._load_opcodes()

    def _load_opcodes(self) -> Dict[int, str]:
        table = {
            0x00: "STOP",
            0x01: "ADD",
            0x02: "MUL",
            0x03: "SUB",
            0x10: "LT",
            0x14: "EQ",
            0x15: "ISZERO",
            0x33: "CALLER",
            0x34: "CALLVALUE",
            0x35: "CALLDATALOAD",
            0x36: "CALLDATASIZE",
            0x37: "CALLDATACOPY",
            0x39: "CODECOPY",
            0x3B: "EXTCODESIZE",
            0x3C: "EXTCODECOPY",
            0x51: "MLOAD",
            0x52: "MSTORE",
            0x53: "MSTORE8",
            0x54: "SLOAD",
            0x55: "SSTORE",
            0x56: "JUMP",
            0x57: "JUMPI",
            0x5B: "JUMPDEST",
            0x60: "PUSH1",
            0x61: "PUSH2",
            0x62: "PUSH3",
            0x63: "PUSH4",
            0x64: "PUSH5",
            0x65: "PUSH6",
            0x66: "PUSH7",
            0x67: "PUSH8",
            0x68: "PUSH9",
            0x69: "PUSH10",
            0x6A: "PUSH11",
            0x6B: "PUSH12",
            0x6C: "PUSH13",
            0x6D: "PUSH14",
            0x6E: "PUSH15",
            0x6F: "PUSH16",
            0x70: "PUSH17",
            0x71: "PUSH18",
            0x72: "PUSH19",
            0x73: "PUSH20",
            0x74: "PUSH21",
            0x75: "PUSH22",
            0x76: "PUSH23",
            0x77: "PUSH24",
            0x78: "PUSH25",
            0x79: "PUSH26",
            0x7A: "PUSH27",
            0x7B: "PUSH28",
            0x7C: "PUSH29",
            0x7D: "PUSH30",
            0x7E: "PUSH31",
            0x7F: "PUSH32",
            0x80: "DUP1",
            0x81: "DUP2",
            0x90: "SWAP1",
            0x91: "SWAP2",
            0xF0: "CREATE",
            0xF1: "CALL",
            0xF2: "CALLCODE",
            0xF3: "RETURN",
            0xF4: "DELEGATECALL",
            0xFA: "STATICCALL",
        }
        return table

    def _normalise_bytes(self, script: Any) -> bytes:
        if isinstance(script, bytes):
            return script
        if isinstance(script, str):
            cleaned = script.strip()
            if cleaned.startswith("0x"):
                cleaned = cleaned[2:]
            cleaned = cleaned.replace(" ", "").replace("\n", "")
            if len(cleaned) % 2 != 0:
                raise ScriptDecodingError("hex calldata must have an even number of characters")
            try:
                return bytes.fromhex(cleaned)
            except ValueError as exc:
                raise ScriptDecodingError("unable to parse Ethereum script as hexadecimal") from exc
        if isinstance(script, Iterable):
            combined = "".join(str(part).strip() for part in script)
            return self._normalise_bytes(combined)
        raise ScriptDecodingError("unsupported Ethereum script input type")

    def _decode_calldata(self, payload: bytes) -> ScriptDecodingResult:
        if len(payload) < 4:
            raise ScriptDecodingError("calldata must contain at least a 4-byte function selector")

        selector = payload[:4].hex()
        args: List[str] = []
        for offset in range(4, len(payload), 32):
            args.append(payload[offset : offset + 32].hex())

        metadata = {
            "format": "calldata",
            "function_selector": selector,
            "argument_count": len(args),
            "arguments": args,
        }

        return ScriptDecodingResult(
            chain=self.chain,
            addresses=[],
            opcode_trace=[f"ARG{i}" for i in range(len(args))],
            metadata=metadata,
        )

    def decode(self, script: Any, **kwargs: Any) -> ScriptDecodingResult:
        mode = kwargs.get("mode", "bytecode")
        payload = self._normalise_bytes(script)

        if mode == "calldata":
            return self._decode_calldata(payload)

        trace: List[str] = []
        idx = 0
        while idx < len(payload):
            opcode = payload[idx]
            name = self._opcodes.get(opcode, f"OP_{opcode:02X}")
            if 0x60 <= opcode <= 0x7F:
                push_len = opcode - 0x5F
                data = payload[idx + 1 : idx + 1 + push_len]
                trace.append(f"{name} 0x{data.hex()}")
                idx += 1 + push_len
                continue
            trace.append(name)
            idx += 1

        metadata = {
            "format": "bytecode",
            "length_bytes": len(payload),
        }
        if payload:
            metadata["entry_opcode"] = trace[0]

        return ScriptDecodingResult(
            chain=self.chain,
            addresses=[],
            opcode_trace=trace,
            metadata=metadata,
        )


# -- Solana ------------------------------------------------------------------


class SolanaScriptDecoder(ScriptDecoder):
    chain = "solana"

    def _normalise(self, script: Any) -> tuple[bytes, Dict[str, Any], List[str]]:
        accounts: List[str] = []
        program_id: Optional[str] = None
        if isinstance(script, Mapping):
            program_id = script.get("program_id")
            accounts = list(script.get("accounts", []))
            data = script.get("data", b"")
            hints = {
                key: value
                for key, value in script.items()
                if key not in {"program_id", "accounts", "data"}
            }
        else:
            data = script
            hints = {}

        payload = self._to_bytes(data)
        metadata = {
            "format": "bpf" if not hints else "anchor_idl",
        }
        if program_id:
            metadata["program_id"] = program_id
        if accounts:
            metadata["account_count"] = len(accounts)
        metadata.update(hints)
        return payload, metadata, accounts

    def _to_bytes(self, data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            cleaned = data.strip()
            try:
                return base64.b64decode(cleaned)
            except Exception:
                pass
            try:
                return bytes.fromhex(cleaned)
            except ValueError:
                pass
            return cleaned.encode("utf8")
        if isinstance(data, Iterable):
            return self._to_bytes("".join(str(part) for part in data))
        raise ScriptDecodingError("unsupported Solana instruction representation")

    def decode(self, script: Any, **kwargs: Any) -> ScriptDecodingResult:
        payload, metadata, accounts = self._normalise(script)
        trace: List[str] = []
        for index, byte in enumerate(payload):
            if index >= 32:
                trace.append("…")
                break
            trace.append(f"BYTE_{byte:02X}")

        metadata.setdefault("data_length", len(payload))

        return ScriptDecodingResult(
            chain=self.chain,
            addresses=[addr for addr in accounts if isinstance(addr, str)],
            opcode_trace=trace,
            metadata=metadata,
        )


# Register default decoders
registry.register(BitcoinScriptDecoder())
registry.register(EthereumScriptDecoder())
registry.register(SolanaScriptDecoder())


def decode_script(chain: str, script: Any, **kwargs: Any) -> ScriptDecodingResult:
    """Decode ``script`` using the decoder registered for ``chain``."""

    return registry.decode(chain, script, **kwargs)


__all__ = [
    "BitcoinScriptDecoder",
    "EthereumScriptDecoder",
    "PkScriptError",
    "ScriptDecoder",
    "ScriptDecoderRegistry",
    "ScriptDecodingError",
    "ScriptDecodingResult",
    "SolanaScriptDecoder",
    "decode_script",
    "registry",
]

