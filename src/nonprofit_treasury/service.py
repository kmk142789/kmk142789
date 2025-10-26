"""Backend utilities for orchestrating NonprofitTreasury smart-contract flows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
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
