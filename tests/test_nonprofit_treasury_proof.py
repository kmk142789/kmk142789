import hashlib
import json
from pathlib import Path

from nonprofit_treasury import TreasuryConfig, NonprofitTreasuryService
from nonprofit_treasury.ledger import TreasuryLedgerEntry
from scripts import nonprofit_treasury_backend as treasury_cli


class _CallResult:
    def __init__(self, value):
        self._value = value

    def call(self):
        return self._value


class _FakeTreasuryFunctions:
    def __init__(self, *, donations: int, disbursed: int, beneficiary: str):
        self._donations = donations
        self._disbursed = disbursed
        self._beneficiary = beneficiary

    def totalDonations(self):  # noqa: N802 - mirrors contract ABI
        return _CallResult(self._donations)

    def totalDisbursed(self):  # noqa: N802 - mirrors contract ABI
        return _CallResult(self._disbursed)

    def getDonationCount(self):  # noqa: N802 - mirrors contract ABI
        return _CallResult(0)

    def beneficiary(self):
        return _CallResult(self._beneficiary)


class _FakeTokenFunctions:
    def __init__(self, *, balance: int):
        self._balance = balance

    def balanceOf(self, _address):  # noqa: N802 - mirrors contract ABI
        return _CallResult(self._balance)


class _FakeContract:
    def __init__(self, functions):
        self.functions = functions
        self.address = "0x0000000000000000000000000000000000000000"
        self.events = type("Events", (), {})()


class _FakeEth:
    def __init__(self, contracts):
        self._contracts = list(contracts)

    def contract(self, *, address=None, abi=None):  # noqa: ANN001
        contract = self._contracts.pop(0)
        contract.address = address or contract.address
        return contract

    def get_block(self, _block_number):  # noqa: ANN001
        return {"timestamp": 0}


class _FakeWeb3:
    def __init__(self, contracts):
        self.eth = _FakeEth(contracts)


def _build_service(tmp_path: Path) -> tuple[TreasuryConfig, NonprofitTreasuryService]:
    config = TreasuryConfig(
        rpc_url="http://localhost:8545",
        contract_address="0x00000000000000000000000000000000000000aA",
        stablecoin_address="0x00000000000000000000000000000000000000bB",
        beneficiary_wallet="0x00000000000000000000000000000000000000Cc",
        treasurer_private_key="0xdeadbeef",
        ledger_path=tmp_path / "treasury.json",
    )

    contracts = [
        _FakeContract(
            _FakeTreasuryFunctions(
                donations=2_500_000,
                disbursed=750_000,
                beneficiary=config.beneficiary_wallet,
            )
        ),
        _FakeContract(_FakeTokenFunctions(balance=1_750_000)),
    ]
    service = NonprofitTreasuryService(config, web3=_FakeWeb3(contracts))

    service.ledger.append(
        TreasuryLedgerEntry(
            type="donation",
            amount=2_500_000,
            token_address=config.stablecoin_address,
            tx_hash="0x01",
            actor="donor",
            timestamp=1,
            memo="seed",
        )
    )
    service.ledger.append(
        TreasuryLedgerEntry(
            type="disbursement",
            amount=750_000,
            token_address=config.stablecoin_address,
            tx_hash="0x02",
            actor="Little Footsteps",
            timestamp=2,
            reason="operations",
        )
    )
    return config, service


def test_generate_proof_links_funds_to_little_footsteps(tmp_path: Path) -> None:
    config, service = _build_service(tmp_path)

    proof = service.generate_proof()

    assert proof.beneficiary_label == "Little Footsteps"
    assert proof.little_footsteps_linked is True
    assert proof.contract_address.lower() == config.contract_address.lower()
    assert proof.stablecoin_address.lower() == config.stablecoin_address.lower()
    assert proof.ledger_balance == service.ledger.balance()
    assert proof.balance_delta == service.ledger.balance() - proof.onchain_balance

    payload = proof.as_dict()
    canonical = {k: v for k, v in payload.items() if k != "proof_hash"}
    recalculated = "sha256:" + hashlib.sha256(
        json.dumps(canonical, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert recalculated == proof.proof_hash


def test_cli_writes_timestamped_proof_snapshot(tmp_path: Path) -> None:
    payload = {"proof_hash": "sha256:deadbeef", "produced_at": "2024-05-01T12:34:56.789Z"}
    destination = treasury_cli.write_proof_snapshot(
        payload,
        payload["produced_at"],
        directory=tmp_path,
    )

    assert destination.name == "little-footsteps-proof-20240501T123456789Z.json"
    saved = json.loads(destination.read_text())
    assert saved == payload


def test_launch_first_beneficiary_flow_returns_manifest(tmp_path: Path) -> None:
    config, service = _build_service(tmp_path)

    manifest = service.launch_first_beneficiary_flow(memo="first launch")

    assert manifest["flow"] == "treasury→beneficiary"
    assert manifest["beneficiary_wallet"].lower() == config.beneficiary_wallet.lower()
    assert manifest["little_footsteps_linked"] is True
    assert manifest["memo"] == "first launch"
    assert manifest["treasury_balance"] == 1_750_000
    assert manifest["proof_hash"].startswith("sha256:")


def test_write_launch_manifest_persists_payload(tmp_path: Path) -> None:
    payload = {"flow": "treasury→beneficiary", "memo": "first launch"}
    destination = treasury_cli.write_launch_manifest(
        payload, destination=tmp_path / "beneficiary_flow.json"
    )

    assert destination.name == "beneficiary_flow.json"
    saved = json.loads(destination.read_text())
    assert saved == payload
