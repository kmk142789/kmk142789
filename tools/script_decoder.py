"""Cross-chain script decoding utilities.

This module provides a unified interface for decoding script-like payloads
across multiple blockchain environments.  A decoder normalises the shape of
its output so that tooling can consume chain-specific metadata without needing
specialised knowledge of how each chain represents scripts or call data.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from verifier.pkscript_registry import canonicalise_tokens


@dataclass(slots=True)
class DecodedScript:
    """Normalised representation of a decoded script."""

    chain: str
    address: str | None
    opcodes: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable dictionary view of the decoded script."""

        payload: dict[str, Any] = {
            "chain": self.chain,
            "opcodes": list(self.opcodes),
            "metadata": dict(self.metadata),
        }
        if self.address is not None:
            payload["address"] = self.address
        return payload


class ScriptDecoder:
    """Base interface implemented by chain specific decoders."""

    chain: str

    def decode(self, script: Iterable[str] | str | bytes, **kwargs: Any) -> DecodedScript:
        """Return a :class:`DecodedScript` for ``script``."""

        raise NotImplementedError


# ---------------------------------------------------------------------------
# Bitcoin decoder implementation

import hashlib
import string


_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_GENERATORS = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


def _is_hex_string(value: str) -> bool:
    return bool(value) and all(char in string.hexdigits for char in value)


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


class PkScriptError(ValueError):
    """Raised when a script does not match the expected formats."""


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
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return _base58_encode(data + checksum)


def _normalise_lines(lines: Iterable[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def _hash160(data: bytes) -> bytes:
    sha = hashlib.sha256(data).digest()
    return hashlib.new("ripemd160", sha).digest()


def _convertbits(data: bytes, from_bits: int, to_bits: int, *, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    result: list[int] = []
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


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(ch) >> 5 for ch in hrp] + [0] + [ord(ch) & 31 for ch in hrp]


def _create_bech32_checksum(hrp: str, data: Iterable[int], const: int) -> list[int]:
    values = _bech32_hrp_expand(hrp) + list(data)
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - idx)) & 31 for idx in range(6)]


def _bech32_encode(hrp: str, data: Iterable[int], *, spec: str = "bech32") -> str:
    const = 1 if spec == "bech32" else 0x2BC830A3
    combined = list(data) + _create_bech32_checksum(hrp, data, const)
    return hrp + "1" + "".join(_BECH32_ALPHABET[d] for d in combined)


def _collect_hex_tokens(tokens: list[str]) -> tuple[str, int]:
    collected: list[str] = []
    for token in tokens:
        if _is_hex_string(token):
            collected.append(token)
        else:
            break
    return "".join(collected), len(collected)


def _pkscript_to_hash(lines: Iterable[str]) -> tuple[str, str, int | None, list[str]]:
    sequence = canonicalise_tokens(_normalise_lines(lines))

    if sequence and _looks_like_base58(sequence[0]):
        sequence = sequence[1:]

    if sequence and sequence[0].lower() == "pkscript":
        sequence = sequence[1:]

    if (
        len(sequence) == 1
        and _is_hex_string(sequence[0])
        and len(sequence[0]) % 2 == 0
    ):
        script_bytes = bytes.fromhex(sequence[0])

        if (
            len(script_bytes) == 25
            and script_bytes[:3] == b"\x76\xa9\x14"
            and script_bytes[-2:] == b"\x88\xac"
        ):
            hash_hex = script_bytes[3:-2].hex()
            canonical = [
                "OP_DUP",
                "OP_HASH160",
                hash_hex,
                "OP_EQUALVERIFY",
                "OP_CHECKSIG",
            ]
            return "p2pkh", hash_hex, None, canonical

        if (
            len(script_bytes) == 23
            and script_bytes[:2] == b"\xa9\x14"
            and script_bytes[-1] == 0x87
        ):
            hash_hex = script_bytes[2:-1].hex()
            canonical = ["OP_HASH160", hash_hex, "OP_EQUAL"]
            return "p2sh", hash_hex, None, canonical

        if len(script_bytes) in {22, 34} and len(script_bytes) >= 4:
            opcode = script_bytes[0]
            length = script_bytes[1]
            program = script_bytes[2:]
            if length != len(program):
                raise PkScriptError("witness program push length mismatch")
            if opcode == 0:
                opcode = "OP_0"
                witness_version = 0
            elif 0x51 <= opcode <= 0x60:
                witness_version = opcode - 0x50
                opcode = f"OP_{witness_version}"
            else:
                raise PkScriptError("unsupported witness version opcode")

            if len(program) == 20:
                script_type = "p2wpkh"
            elif len(program) == 32:
                script_type = "p2tr" if witness_version == 1 else "p2wsh"
            else:
                raise PkScriptError("unsupported witness program length for address conversion")

            canonical = [opcode, program.hex()]
            return script_type, program.hex(), witness_version, canonical

    expected = [
        "OP_DUP",
        "OP_HASH160",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    if len(sequence) == 5 and sequence[0:2] == expected[:2] and sequence[3:] == expected[2:]:
        hash_candidate = sequence[2]

        if len(hash_candidate) != 40:
            raise PkScriptError("pubkey hash must be 20 bytes of hex")

        try:
            bytes.fromhex(hash_candidate)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise PkScriptError("pubkey hash must be hexadecimal") from exc

        return "p2pkh", hash_candidate, None, sequence

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

        return "p2pkh", _hash160(pubkey_bytes).hex(), None, sequence

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

        return "p2sh", hash_candidate, None, sequence

    if sequence:
        version_token = sequence[0].upper()
        witness_version: int | None
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
                return "p2wpkh", program_hex, witness_version, sequence
            if len(program) == 32:
                script_type = "p2tr" if witness_version == 1 else "p2wsh"
                return script_type, program_hex, witness_version, sequence

            raise PkScriptError("unsupported witness program length for address conversion")

    raise PkScriptError("unsupported script layout for address conversion")


class BitcoinScriptDecoder(ScriptDecoder):
    """Decode legacy and segwit Bitcoin scripts into addresses."""

    chain = "bitcoin"

    _NETWORKS: Mapping[str, Mapping[str, object]] = {
        "mainnet": {"p2pkh": 0x00, "p2sh": 0x05, "bech32_hrp": "bc"},
        "testnet": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "tb"},
        "regtest": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "bcrt"},
    }

    def decode(
        self,
        script: Iterable[str] | str | bytes,
        *,
        network: str = "mainnet",
    ) -> DecodedScript:
        if isinstance(script, bytes):
            lines: Sequence[str] = [script.hex()]
        elif isinstance(script, str):
            lines = script.splitlines()
        else:
            lines = list(script)

        try:
            script_versions = self._NETWORKS[network.lower()]
        except KeyError as exc:
            raise ValueError(f"unknown network '{network}'") from exc

        script_type, hash_hex, witness_version, sequence = _pkscript_to_hash(lines)

        address: str | None
        metadata: dict[str, Any] = {
            "network": network.lower(),
            "script_type": script_type,
            "hash_hex": hash_hex,
        }

        if script_type in {"p2pkh", "p2sh"}:
            version = script_versions[script_type]  # type: ignore[index]
            address = _base58check_encode(int(version), bytes.fromhex(hash_hex))
        elif script_type in {"p2wpkh", "p2wsh", "p2tr"}:
            hrp = script_versions.get("bech32_hrp")
            if not isinstance(hrp, str):
                raise PkScriptError("network does not define a bech32 HRP")
            if witness_version is None:
                raise PkScriptError("missing witness version for segwit script")
            address = _bech32_encode(
                hrp,
                [witness_version]
                + _convertbits(bytes.fromhex(hash_hex), 8, 5, pad=True),
                spec="bech32" if witness_version == 0 else "bech32m",
            )
            metadata["witness_version"] = witness_version
        else:
            raise PkScriptError(f"unsupported script type '{script_type}'")

        return DecodedScript(
            chain=self.chain,
            address=address,
            opcodes=[token.upper() for token in sequence],
            metadata=metadata,
        )


# ---------------------------------------------------------------------------
# Ethereum decoder implementation

_EVM_OPCODE_TABLE: MutableMapping[int, str] = {}


def _load_evm_opcodes() -> None:
    if _EVM_OPCODE_TABLE:
        return

    search_paths = (
        Path(__file__).resolve().parent / ".." / "data" / "evm_opcodes.json",
        Path(__file__).resolve().parent / "../data/evm_opcodes.json",
        Path(__file__).resolve().parent / "../../data/evm_opcodes.json",
    )
    for path in search_paths:
        if path.exists():
            with path.open("r", encoding="utf8") as handle:
                raw = json.load(handle)
            for opcode_hex, name in raw.items():
                try:
                    opcode = int(opcode_hex, 16)
                except ValueError:
                    continue
                if isinstance(name, str):
                    _EVM_OPCODE_TABLE[opcode] = name
            break

    if not _EVM_OPCODE_TABLE:
        # Provide a minimal fallback so that decoding still works in tests
        _EVM_OPCODE_TABLE.update(
            {
                0x00: "STOP",
                0x01: "ADD",
                0x52: "MSTORE",
                0x56: "JUMP",
                0x57: "JUMPI",
                0x5B: "JUMPDEST",
                0x60: "PUSH1",
                0x61: "PUSH2",
                0x7F: "PUSH32",
                0xF1: "CALL",
                0xFD: "REVERT",
                0xFE: "INVALID",
                0xFF: "SELFDESTRUCT",
            }
        )


class EthereumScriptDecoder(ScriptDecoder):
    """Decode simple snippets of EVM bytecode or ABI call data."""

    chain = "ethereum"

    def decode(
        self,
        script: Iterable[str] | str | bytes,
        *,
        chain_id: int | None = None,
    ) -> DecodedScript:
        if isinstance(script, bytes):
            data = script
        elif isinstance(script, str):
            cleaned = script.strip()
            if cleaned.startswith("0x"):
                cleaned = cleaned[2:]
            cleaned = "".join(cleaned.split())
            if len(cleaned) % 2:
                raise ValueError("hex string must contain an even number of characters")
            data = bytes.fromhex(cleaned)
        else:
            concatenated = "".join(str(part).strip() for part in script)
            if concatenated.startswith("0x"):
                concatenated = concatenated[2:]
            if len(concatenated) % 2:
                raise ValueError("hex string must contain an even number of characters")
            data = bytes.fromhex(concatenated)

        metadata: dict[str, Any] = {
            "byte_length": len(data),
        }
        if chain_id is not None:
            metadata["chain_id"] = chain_id

        hex_payload = data.hex()
        opcodes: list[str] = []

        # Detect ABI call data (4 byte selector + N*32 byte arguments)
        if len(data) >= 4 and (len(data) - 4) % 32 == 0:
            selector = data[:4].hex()
            arguments = [data[idx : idx + 32].hex() for idx in range(4, len(data), 32)]
            metadata.update(
                {
                    "call_type": "contract_call",
                    "function_selector": f"0x{selector}",
                    "argument_words": [f"0x{word}" for word in arguments],
                }
            )
            opcodes.append(f"CALLDATA_SELECTOR 0x{selector}")
            for word in arguments:
                opcodes.append(f"CALLDATA_ARG 0x{word}")
            return DecodedScript(
                chain=self.chain,
                address=None,
                opcodes=opcodes,
                metadata=metadata,
            )

        _load_evm_opcodes()

        idx = 0
        while idx < len(data):
            opcode = data[idx]
            idx += 1
            name = _EVM_OPCODE_TABLE.get(opcode, f"UNKNOWN_{opcode:#02x}")
            if 0x60 <= opcode <= 0x7F:
                push_length = opcode - 0x5F
                argument = data[idx : idx + push_length]
                idx += push_length
                opcodes.append(f"{name} 0x{argument.hex()}")
            else:
                opcodes.append(name)

        metadata["bytecode_hex"] = f"0x{hex_payload}"

        return DecodedScript(
            chain=self.chain,
            address=None,
            opcodes=opcodes,
            metadata=metadata,
        )


# ---------------------------------------------------------------------------
# Solana decoder implementation

class SolanaScriptDecoder(ScriptDecoder):
    """Decode Anchor-style Solana instruction payloads."""

    chain = "solana"

    def decode(
        self,
        script: Iterable[str] | str | bytes | Mapping[str, Any],
        *,
        program_id: str | None = None,
    ) -> DecodedScript:
        payload: Mapping[str, Any]
        if isinstance(script, Mapping):
            payload = script
        elif isinstance(script, bytes):
            payload = {"data": base64.b64encode(script).decode("ascii")}
        elif isinstance(script, str):
            cleaned = script.strip()
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError:
                payload = {"data": cleaned}
            else:
                if isinstance(parsed, Mapping):
                    payload = parsed  # type: ignore[assignment]
                else:
                    raise ValueError("JSON Solana payload must decode to an object")
        else:
            items = list(script)
            if len(items) == 3:
                payload = {"program_id": items[0], "accounts": items[1], "data": items[2]}
            else:
                raise ValueError("Iterable Solana payload must contain program_id, accounts, and data")

        program = payload.get("program_id") or program_id or ""
        accounts = payload.get("accounts")
        if isinstance(accounts, str):
            accounts_list = [acc.strip() for acc in accounts.split(",") if acc.strip()]
        elif isinstance(accounts, Sequence):
            accounts_list = [str(acc) for acc in accounts]
        else:
            accounts_list = []

        raw_data = payload.get("data", "")
        if isinstance(raw_data, str):
            cleaned = raw_data.strip()
            try:
                data_bytes = base64.b64decode(cleaned)
            except (ValueError, binascii.Error):  # type: ignore[name-defined]
                try:
                    data_bytes = bytes.fromhex(cleaned)
                except ValueError:
                    data_bytes = cleaned.encode("utf8")
        elif isinstance(raw_data, bytes):
            data_bytes = raw_data
        else:
            data_bytes = json.dumps(raw_data, ensure_ascii=False).encode("utf8")

        opcode_hint = None
        if data_bytes:
            opcode_hint = f"0x{data_bytes[0]:02x}"

        metadata: dict[str, Any] = {
            "program_id": program,
            "account_count": len(accounts_list),
            "data_length": len(data_bytes),
            "accounts": accounts_list,
        }
        if opcode_hint is not None:
            metadata["instruction_discriminator"] = opcode_hint

        opcodes = [f"ACCOUNT {account}" for account in accounts_list]
        if opcode_hint is not None:
            opcodes.append(f"INSTRUCTION 0x{data_bytes.hex()}")
        else:
            opcodes.append("INSTRUCTION <empty>")

        return DecodedScript(
            chain=self.chain,
            address=None,
            opcodes=opcodes,
            metadata=metadata,
        )


# ---------------------------------------------------------------------------
# Registry helpers

_bitcoin_decoder = BitcoinScriptDecoder()
_ethereum_decoder = EthereumScriptDecoder()
_solana_decoder = SolanaScriptDecoder()

_DECODER_REGISTRY: dict[str, ScriptDecoder] = {
    "bitcoin": _bitcoin_decoder,
    "btc": _bitcoin_decoder,
    "ethereum": _ethereum_decoder,
    "eth": _ethereum_decoder,
    "solana": _solana_decoder,
    "sol": _solana_decoder,
}


def get_decoder(chain: str) -> ScriptDecoder:
    """Return a decoder for ``chain``."""

    key = chain.lower()
    decoder = _DECODER_REGISTRY.get(key)
    if decoder is None:
        raise ValueError(f"no decoder registered for chain '{chain}'")
    return decoder


def decode_script(chain: str, script: Iterable[str] | str | bytes, **kwargs: Any) -> DecodedScript:
    """Convenience helper that routes to :func:`get_decoder`."""

    decoder = get_decoder(chain)
    return decoder.decode(script, **kwargs)
