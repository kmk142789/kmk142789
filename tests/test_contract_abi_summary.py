from __future__ import annotations

from echo.crypto.abi_summary import summarize_abi

ABI = [
    {"inputs": [], "payable": False, "stateMutability": "nonpayable", "type": "constructor"},
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previousAddress", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newAddress", "type": "address"},
        ],
        "name": "ChildChainChanged",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "input1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "output1", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "input1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "input2", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "output1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "output2", "type": "uint256"},
        ],
        "name": "LogFeeTransfer",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "input1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "input2", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "output1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "output2", "type": "uint256"},
        ],
        "name": "LogTransfer",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previousOwner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newOwner", "type": "address"},
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previousAddress", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newAddress", "type": "address"},
        ],
        "name": "ParentChanged",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "input1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "output1", "type": "uint256"},
        ],
        "name": "Withdraw",
        "type": "event",
    },
    {"constant": True, "inputs": [], "name": "CHAINID", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "EIP712_DOMAIN_HASH", "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "EIP712_DOMAIN_SCHEMA_HASH", "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "EIP712_TOKEN_TRANSFER_ORDER_SCHEMA_HASH", "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "address", "name": "newAddress", "type": "address"}], "name": "changeChildChain", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [], "name": "childChain", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "currentSupply", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "payable": False, "stateMutability": "pure", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "address", "name": "user", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "deposit", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "name": "disabledHashes", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [{"internalType": "bytes32", "name": "hash", "type": "bytes32"}, {"internalType": "bytes", "name": "sig", "type": "bytes"}], "name": "ecrecovery", "outputs": [{"internalType": "address", "name": "result", "type": "address"}], "payable": False, "stateMutability": "pure", "type": "function"},
    {"constant": True, "inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "tokenIdOrAmount", "type": "uint256"}, {"internalType": "bytes32", "name": "data", "type": "bytes32"}, {"internalType": "uint256", "name": "expiration", "type": "uint256"}], "name": "getTokenTransferOrderHash", "outputs": [{"internalType": "bytes32", "name": "orderHash", "type": "bytes32"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "address", "name": "_childChain", "type": "address"}, {"internalType": "address", "name": "_token", "type": "address"}], "name": "initialize", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [], "name": "isOwner", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "payable": False, "stateMutability": "pure", "type": "function"},
    {"constant": True, "inputs": [], "name": "networkId", "outputs": [{"internalType": "bytes", "name": "", "type": "bytes"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "parent", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [], "name": "renounceOwnership", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "setParent", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "payable": False, "stateMutability": "pure", "type": "function"},
    {"constant": True, "inputs": [], "name": "token", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "payable": False, "stateMutability": "pure", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "value", "type": "uint256"}], "name": "transfer", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "payable": True, "stateMutability": "payable", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}], "name": "transferOwnership", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "bytes", "name": "sig", "type": "bytes"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}, {"internalType": "bytes32", "name": "data", "type": "bytes32"}, {"internalType": "uint256", "name": "expiration", "type": "uint256"}, {"internalType": "address", "name": "to", "type": "address"}], "name": "transferWithSig", "outputs": [{"internalType": "address", "name": "from", "type": "address"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": False, "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [], "payable": True, "stateMutability": "payable", "type": "function"},
]


def test_summarize_abi_provides_signature_overview() -> None:
    summary = summarize_abi(ABI)

    assert summary.constructor is not None
    assert summary.constructor.signature == "constructor()"
    assert not summary.has_fallback
    assert not summary.has_receive

    function_signatures = summary.function_signatures()
    assert function_signatures["deposit"] == ("deposit(address,uint256)",)
    assert function_signatures["withdraw"] == ("withdraw(uint256)",)
    assert summary.functions["transfer"][0].state_mutability == "payable"
    assert not summary.functions["transfer"][0].constant
    assert summary.functions["balanceOf"][0].outputs[0].name == "ret0"


def test_event_metadata_preserves_indexing_information() -> None:
    summary = summarize_abi(ABI)

    log_transfer = summary.events["LogTransfer"][0]
    assert log_transfer.signature == "LogTransfer(address,address,address,uint256,uint256,uint256,uint256,uint256)"
    indexed_flags = [param.indexed for param in log_transfer.inputs]
    assert indexed_flags[:3] == [True, True, True]
    assert indexed_flags[3:] == [False, False, False, False, False]

    deposit_event = summary.events["Deposit"][0]
    assert deposit_event.inputs[0].name == "token"
    assert not deposit_event.inputs[-1].indexed
