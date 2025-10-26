"""Backend utilities for orchestrating NonprofitBank smart-contract flows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Sequence

from web3 import Web3
from web3.contract import Contract

from .config import BankConfig
from .ledger import Ledger, LedgerEntry

logger = logging.getLogger(__name__)


NONPROFIT_BANK_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_lilFootsteps", "type": "address"},
            {"internalType": "uint256", "name": "_payoutInterval", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previous", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "current", "type": "address"},
        ],
        "name": "LilFootstepsUpdated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "uint256", "name": "previousInterval", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "currentInterval", "type": "uint256"},
        ],
        "name": "PayoutPolicyUpdated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "triggeredBy", "type": "address"},
        ],
        "name": "PayoutExecuted",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "canTriggerPayout",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getBalance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "triggerPayout",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


@dataclass
class ProcessedEvent:
    tx_hash: str
    block_number: int


class NonprofitBankService:
    """High-level orchestration that keeps on-chain state and the ledger in sync."""

    def __init__(self, config: BankConfig, *, web3: Web3 | None = None) -> None:
        self.config = config
        self.web3 = web3 or Web3(Web3.HTTPProvider(config.rpc_url))
        self.contract: Contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(config.contract_address), abi=NONPROFIT_BANK_ABI
        )
        self.ledger = Ledger(config.ledger_path)

    # ------------------------------------------------------------------
    # Deposit tracking
    # ------------------------------------------------------------------
    def sync_deposits(self, *, from_block: int, to_block: int | str = "latest") -> Sequence[ProcessedEvent]:
        """Pull Deposit events from the chain and record them locally."""

        deposit_event = self.contract.events.Deposit
        events = deposit_event.get_logs(fromBlock=from_block, toBlock=to_block)
        processed: list[ProcessedEvent] = []
        for event in events:
            args = event["args"]
            entry = LedgerEntry(
                type="deposit",
                amount_wei=int(args["amount"]),
                tx_hash=event["transactionHash"].hex(),
                actor=args["from"],
                timestamp=int(args["timestamp"]),
            )
            self.ledger.append(entry)
            processed.append(ProcessedEvent(tx_hash=entry.tx_hash, block_number=event["blockNumber"]))
            logger.info("Recorded deposit from %s for %s wei", entry.actor, entry.amount_wei)
        return processed

    # ------------------------------------------------------------------
    # Payout automation
    # ------------------------------------------------------------------
    def can_trigger_payout(self) -> bool:
        return bool(self.contract.functions.canTriggerPayout().call())

    def trigger_payout(self) -> str:
        """Trigger the smart-contract payout and log the event."""

        if not self.can_trigger_payout():
            raise RuntimeError("Payout interval has not elapsed or there are no funds to transfer.")

        account = self.web3.eth.account.from_key(self.config.owner_private_key)
        nonce = self.web3.eth.get_transaction_count(account.address)
        txn = self.contract.functions.triggerPayout().build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": 350000,
                "maxFeePerGas": self.web3.to_wei("30", "gwei"),
                "maxPriorityFeePerGas": self.web3.to_wei("2", "gwei"),
            }
        )
        signed = account.sign_transaction(txn)
        tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        payout_events = self.contract.events.PayoutExecuted().process_receipt(receipt)
        for event in payout_events:
            args = event["args"]
            entry = LedgerEntry(
                type="payout",
                amount_wei=int(args["amount"]),
                tx_hash=tx_hash.hex(),
                actor=args["triggeredBy"],
                timestamp=int(args["timestamp"]),
            )
            self.ledger.append(entry)
            logger.info("Payout of %s wei triggered by %s", entry.amount_wei, entry.actor)

        return tx_hash.hex()

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def current_balance(self) -> int:
        return int(self.contract.functions.getBalance().call())

    def ledger_entries(self) -> Iterable[LedgerEntry]:
        return self.ledger.entries()
