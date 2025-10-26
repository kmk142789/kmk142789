"""Configuration helpers for the NonprofitTreasury backend."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class TreasuryConfig:
    """Runtime configuration for interacting with the NonprofitTreasury contract."""

    rpc_url: str
    contract_address: str
    stablecoin_address: str
    beneficiary_wallet: str
    treasurer_private_key: str
    ledger_path: Path

    @classmethod
    def from_env(cls, *, env: Dict[str, str] | None = None) -> "TreasuryConfig":
        env = env or os.environ
        ledger_path = Path(env.get("NONPROFIT_TREASURY_LEDGER_PATH", "ledger/nonprofit_treasury_ledger.json"))
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        return cls(
            rpc_url=env["NONPROFIT_TREASURY_RPC_URL"],
            contract_address=env["NONPROFIT_TREASURY_CONTRACT"],
            stablecoin_address=env["NONPROFIT_TREASURY_STABLECOIN"],
            beneficiary_wallet=env["NONPROFIT_TREASURY_BENEFICIARY"],
            treasurer_private_key=env["NONPROFIT_TREASURY_TREASURER_KEY"],
            ledger_path=ledger_path,
        )

    def dump(self) -> Dict[str, Any]:
        """Serialize the configuration to assist dashboards and debugging."""

        return {
            "rpc_url": self.rpc_url,
            "contract_address": self.contract_address,
            "stablecoin_address": self.stablecoin_address,
            "beneficiary_wallet": self.beneficiary_wallet,
            "ledger_path": str(self.ledger_path),
        }

    def write_snapshot(self, destination: Path | None = None) -> Path:
        destination = destination or self.ledger_path.with_suffix(".config.json")
        destination.write_text(json.dumps(self.dump(), indent=2))
        return destination
