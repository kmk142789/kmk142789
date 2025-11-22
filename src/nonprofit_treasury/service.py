"""Backend utilities for orchestrating NonprofitTreasury smart-contract flows."""

from __future__ import annotations

import logging
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

from web3 import Web3
from web3.contract import Contract

from .config import TreasuryConfig
from .ledger import TreasuryLedger, TreasuryLedgerEntry

logger = logging.getLogger(__name__)


NONPROFIT_TREASURY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "stablecoinAddress", "type": "address"},
            {"internalType": "address", "name": "beneficiaryWallet", "type": "address"},
            {"internalType": "address", "name": "admin", "type": "address"},
        ],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "donor", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "memo", "type": "string"},
        ],
        "name": "DonationReceived",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "beneficiary", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "reason", "type": "string"},
        ],
        "name": "DisbursementExecuted",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "DEFAULT_ADMIN_ROLE",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "grantRole",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "hasRole",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "revokeRole",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "memo", "type": "string"},
        ],
        "name": "donate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "reason", "type": "string"},
        ],
        "name": "disburse",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "stablecoin",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "beneficiary",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalDonations",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalDisbursed",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getDonationCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "newBeneficiary", "type": "address"},
        ],
        "name": "setBeneficiary",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    }
]


@dataclass
class DonationEvent:
    tx_hash: str
    block_number: int
    donor: str
    amount: int
    memo: str


@dataclass
class DisbursementEvent:
    tx_hash: str
    block_number: int
    beneficiary: str
    amount: int
    reason: str


@dataclass(frozen=True)
class TreasuryProof:
    """Immutable snapshot tying the treasury balance to Little Footsteps."""

    produced_at: str
    contract_address: str
    stablecoin_address: str
    beneficiary_wallet: str
    beneficiary_label: str
    contract_beneficiary: str
    little_footsteps_linked: bool
    onchain_balance: int
    total_donations: int
    total_disbursed: int
    ledger_balance: int
    balance_delta: int
    ledger_path: str
    proof_hash: str

    def canonical_payload(self) -> dict[str, object]:
        """Return the payload that is hashed for proof verification."""

        return {
            "produced_at": self.produced_at,
            "contract_address": self.contract_address,
            "stablecoin_address": self.stablecoin_address,
            "beneficiary_wallet": self.beneficiary_wallet,
            "beneficiary_label": self.beneficiary_label,
            "contract_beneficiary": self.contract_beneficiary,
            "little_footsteps_linked": self.little_footsteps_linked,
            "onchain_balance": self.onchain_balance,
            "total_donations": self.total_donations,
            "total_disbursed": self.total_disbursed,
            "ledger_balance": self.ledger_balance,
            "balance_delta": self.balance_delta,
            "ledger_path": self.ledger_path,
        }

    def as_dict(self) -> dict[str, object]:
        payload = dict(self.canonical_payload())
        payload["proof_hash"] = self.proof_hash
        return payload


class NonprofitTreasuryService:
    """Synchronizes the on-chain treasury state with local audit artifacts."""

    def __init__(self, config: TreasuryConfig, *, web3: Web3 | None = None) -> None:
        self.config = config
        self.web3 = web3 or Web3(Web3.HTTPProvider(config.rpc_url))
        self.contract: Contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(config.contract_address), abi=NONPROFIT_TREASURY_ABI
        )
        self.token_address = Web3.to_checksum_address(config.stablecoin_address)
        self.token_contract: Contract = self.web3.eth.contract(
            address=self.token_address, abi=ERC20_ABI
        )
        self.ledger = TreasuryLedger(config.ledger_path)

    # ------------------------------------------------------------------
    # Event synchronization
    # ------------------------------------------------------------------
    def sync_donations(self, *, from_block: int, to_block: int | str = "latest") -> Sequence[DonationEvent]:
        donation_event = self.contract.events.DonationReceived
        events = donation_event.get_logs(fromBlock=from_block, toBlock=to_block)
        processed: list[DonationEvent] = []
        for event in events:
            args = event["args"]
            timestamp = self._timestamp_for_block(event["blockNumber"])
            entry = TreasuryLedgerEntry(
                type="donation",
                amount=int(args["amount"]),
                token_address=self.token_address,
                tx_hash=event["transactionHash"].hex(),
                actor=args["donor"],
                timestamp=timestamp,
                memo=args["memo"],
            )
            self.ledger.append(entry)
            donation = DonationEvent(
                tx_hash=entry.tx_hash,
                block_number=event["blockNumber"],
                donor=args["donor"],
                amount=entry.amount,
                memo=args["memo"],
            )
            processed.append(donation)
            logger.info(
                "Recorded treasury donation from %s for %s tokens (memo=%s)",
                entry.actor,
                entry.amount,
                args["memo"],
            )
        return processed

    def sync_disbursements(
        self, *, from_block: int, to_block: int | str = "latest"
    ) -> Sequence[DisbursementEvent]:
        disbursement_event = self.contract.events.DisbursementExecuted
        events = disbursement_event.get_logs(fromBlock=from_block, toBlock=to_block)
        processed: list[DisbursementEvent] = []
        for event in events:
            args = event["args"]
            timestamp = self._timestamp_for_block(event["blockNumber"])
            entry = TreasuryLedgerEntry(
                type="disbursement",
                amount=int(args["amount"]),
                token_address=self.token_address,
                tx_hash=event["transactionHash"].hex(),
                actor=args["beneficiary"],
                timestamp=timestamp,
                reason=args["reason"],
            )
            self.ledger.append(entry)
            disbursement = DisbursementEvent(
                tx_hash=entry.tx_hash,
                block_number=event["blockNumber"],
                beneficiary=args["beneficiary"],
                amount=entry.amount,
                reason=args["reason"],
            )
            processed.append(disbursement)
            logger.info(
                "Recorded treasury disbursement of %s tokens to %s (reason=%s)",
                entry.amount,
                args["beneficiary"],
                args["reason"],
            )
        return processed

    # ------------------------------------------------------------------
    # State queries and transactions
    # ------------------------------------------------------------------
    def treasury_balance(self) -> int:
        return int(self.token_contract.functions.balanceOf(self.contract.address).call())

    def total_donations(self) -> int:
        return int(self.contract.functions.totalDonations().call())

    def total_disbursed(self) -> int:
        return int(self.contract.functions.totalDisbursed().call())

    def donation_count(self) -> int:
        return int(self.contract.functions.getDonationCount().call())

    def execute_disbursement(self, *, amount: int, reason: str) -> str:
        if amount <= 0:
            raise ValueError("Disbursement amount must be greater than zero")
        if not reason:
            raise ValueError("Reason is required for auditability")

        account = self.web3.eth.account.from_key(self.config.treasurer_private_key)
        nonce = self.web3.eth.get_transaction_count(account.address)
        txn = self.contract.functions.disburse(amount, reason).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": 450000,
                "maxFeePerGas": self.web3.to_wei("30", "gwei"),
                "maxPriorityFeePerGas": self.web3.to_wei("2", "gwei"),
            }
        )
        signed = account.sign_transaction(txn)
        tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        disbursement_events = self.contract.events.DisbursementExecuted().process_receipt(receipt)
        for event in disbursement_events:
            args = event["args"]
            timestamp = self._timestamp_for_block(receipt.blockNumber)
            entry = TreasuryLedgerEntry(
                type="disbursement",
                amount=int(args["amount"]),
                token_address=self.token_address,
                tx_hash=tx_hash.hex(),
                actor=args["beneficiary"],
                timestamp=timestamp,
                reason=args["reason"],
            )
            self.ledger.append(entry)
            logger.info(
                "Disbursed %s tokens to %s via on-chain execution (reason=%s)",
                entry.amount,
                args["beneficiary"],
                args["reason"],
            )

        return tx_hash.hex()

    def set_beneficiary(self, *, new_beneficiary: str) -> str:
        account = self.web3.eth.account.from_key(self.config.treasurer_private_key)
        nonce = self.web3.eth.get_transaction_count(account.address)
        txn = self.contract.functions.setBeneficiary(new_beneficiary).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": 200000,
                "maxFeePerGas": self.web3.to_wei("30", "gwei"),
                "maxPriorityFeePerGas": self.web3.to_wei("2", "gwei"),
            }
        )
        signed = account.sign_transaction(txn)
        tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Updated NonprofitTreasury beneficiary to %s", new_beneficiary)
        return tx_hash.hex()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _timestamp_for_block(self, block_number: int) -> int:
        block = self.web3.eth.get_block(block_number)
        return int(block["timestamp"])

    def ledger_entries(self) -> Iterable[TreasuryLedgerEntry]:
        return self.ledger.entries()

    # ------------------------------------------------------------------
    # Proof generation
    # ------------------------------------------------------------------
    def generate_proof(self, *, beneficiary_label: str = "Little Footsteps") -> TreasuryProof:
        """Produce a verifiable proof of funds bound to Little Footsteps."""

        produced_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

        def _checksum(value: str) -> str:
            try:
                return Web3.to_checksum_address(value)
            except (TypeError, ValueError):
                return value

        contract_address = _checksum(self.config.contract_address)
        stablecoin_address = _checksum(self.config.stablecoin_address)
        beneficiary_wallet = _checksum(self.config.beneficiary_wallet)

        contract_beneficiary_raw = self.contract.functions.beneficiary().call()
        contract_beneficiary = _checksum(contract_beneficiary_raw)

        onchain_balance = self.treasury_balance()
        total_donations = self.total_donations()
        total_disbursed = self.total_disbursed()
        ledger_balance = self.ledger.balance()
        balance_delta = ledger_balance - onchain_balance

        label = beneficiary_label.strip() or "Little Footsteps"
        little_footsteps_linked = label.lower().startswith("little footsteps")
        beneficiary_match = contract_beneficiary.lower() == beneficiary_wallet.lower()
        linked = little_footsteps_linked and beneficiary_match

        payload = {
            "produced_at": produced_at,
            "contract_address": contract_address,
            "stablecoin_address": stablecoin_address,
            "beneficiary_wallet": beneficiary_wallet,
            "beneficiary_label": label,
            "contract_beneficiary": contract_beneficiary,
            "little_footsteps_linked": linked,
            "onchain_balance": onchain_balance,
            "total_donations": total_donations,
            "total_disbursed": total_disbursed,
            "ledger_balance": ledger_balance,
            "balance_delta": balance_delta,
            "ledger_path": str(self.config.ledger_path),
        }

        proof_hash = "sha256:" + hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return TreasuryProof(proof_hash=proof_hash, **payload)

    # ------------------------------------------------------------------
    # Beneficiary pipeline bootstrap
    # ------------------------------------------------------------------
    def launch_first_beneficiary_flow(
        self, *, beneficiary_label: str = "Little Footsteps", memo: str | None = None
    ) -> dict[str, object]:
        """Activate the treasury → beneficiary pipeline and return a manifest payload."""

        proof = self.generate_proof(beneficiary_label=beneficiary_label)
        manifest = {
            "flow": "treasury→beneficiary",
            "beneficiary_label": proof.beneficiary_label,
            "beneficiary_wallet": proof.beneficiary_wallet,
            "contract_address": proof.contract_address,
            "stablecoin_address": proof.stablecoin_address,
            "little_footsteps_linked": proof.little_footsteps_linked,
            "treasury_balance": proof.onchain_balance,
            "total_donations": proof.total_donations,
            "total_disbursed": proof.total_disbursed,
            "ledger_balance": proof.ledger_balance,
            "balance_delta": proof.balance_delta,
            "proof_hash": proof.proof_hash,
            "produced_at": proof.produced_at,
            "memo": memo or "Launch the first beneficiary flow",
        }

        logger.info(
            "Beneficiary flow launched for %s with balance %s tokens (linked=%s)",
            manifest["beneficiary_label"],
            manifest["treasury_balance"],
            manifest["little_footsteps_linked"],
        )
        return manifest
