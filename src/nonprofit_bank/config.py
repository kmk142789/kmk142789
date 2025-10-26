"""Configuration helpers for the NonprofitBank backend."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class BankConfig:
    """Runtime configuration for coordinating the smart-contract workflow."""

    rpc_url: str
    contract_address: str
    owner_private_key: str
    daycare_wallet: str
    ledger_path: Path

    @classmethod
    def from_env(cls, *, env: Dict[str, str] | None = None) -> "BankConfig":
        env = env or os.environ
        ledger_path = Path(env.get("NONPROFIT_LEDGER_PATH", "ledger/nonprofit_bank_ledger.json"))
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        return cls(
            rpc_url=env["NONPROFIT_RPC_URL"],
            contract_address=env["NONPROFIT_CONTRACT_ADDRESS"],
            owner_private_key=env["NONPROFIT_OWNER_KEY"],
            daycare_wallet=env["NONPROFIT_DAYCARE_WALLET"],
            ledger_path=ledger_path,
        )

    def dump(self) -> Dict[str, Any]:
        """Serialize the configuration for debugging or dashboards."""

        return {
            "rpc_url": self.rpc_url,
            "contract_address": self.contract_address,
            "daycare_wallet": self.daycare_wallet,
            "ledger_path": str(self.ledger_path),
        }

    def write_snapshot(self, destination: Path | None = None) -> Path:
        destination = destination or self.ledger_path.with_suffix(".config.json")
        destination.write_text(json.dumps(self.dump(), indent=2))
        return destination
