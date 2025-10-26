// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title NonprofitBank
/// @notice Accepts deposits from nonprofit organizations and escrow them until
///         the configured payout interval elapses. After the interval anyone can
///         trigger an automatic payout to the Lil Footsteps daycare wallet.
/// @dev    The contract is intentionally lightweight so it can be audited and
///         monitored by the community. It emits granular events so a backend
///         service can build a transparent ledger.
contract NonprofitBank {
    /// @notice Emitted whenever funds are deposited by a nonprofit.
    event Deposit(address indexed from, uint256 amount, uint256 timestamp);

    /// @notice Emitted whenever the daycare destination changes.
    event LilFootstepsUpdated(address indexed previous, address indexed current);

    /// @notice Emitted when the payout cadence is updated.
    event PayoutPolicyUpdated(uint256 previousInterval, uint256 currentInterval);

    /// @notice Emitted when a payout transfers funds to Lil Footsteps.
    event PayoutExecuted(uint256 amount, uint256 timestamp, address indexed triggeredBy);

    address public immutable owner;
    address payable public lilFootsteps;

    /// @notice Minimum number of seconds that must elapse between automatic payouts.
    uint256 public payoutInterval;
    uint256 public lastPayoutAt;

    error NotOwner();
    error InvalidAddress();
    error IntervalTooShort();
    error NothingToPayout();
    error IntervalNotElapsed();

    constructor(address payable _lilFootsteps, uint256 _payoutInterval) {
        if (_lilFootsteps == address(0)) {
            revert InvalidAddress();
        }
        if (_payoutInterval < 1 hours) {
            revert IntervalTooShort();
        }
        owner = msg.sender;
        lilFootsteps = _lilFootsteps;
        payoutInterval = _payoutInterval;
        lastPayoutAt = block.timestamp;
        emit LilFootstepsUpdated(address(0), _lilFootsteps);
        emit PayoutPolicyUpdated(0, _payoutInterval);
    }

    /// @notice Accept funds from nonprofits or other supporters.
    function deposit() external payable {
        require(msg.value > 0, "No funds provided");
        emit Deposit(msg.sender, msg.value, block.timestamp);
    }

    /// @notice Allows the owner to update the daycare address if Lil Footsteps
    ///         rotates keys. The change is emitted on-chain for transparency.
    function updateLilFootsteps(address payable _newAddress) external {
        if (msg.sender != owner) revert NotOwner();
        if (_newAddress == address(0)) revert InvalidAddress();
        address previous = lilFootsteps;
        lilFootsteps = _newAddress;
        emit LilFootstepsUpdated(previous, _newAddress);
    }

    /// @notice Updates the payout interval. Restricted to the owner.
    function updatePayoutInterval(uint256 _payoutInterval) external {
        if (msg.sender != owner) revert NotOwner();
        if (_payoutInterval < 1 hours) revert IntervalTooShort();
        uint256 previous = payoutInterval;
        payoutInterval = _payoutInterval;
        emit PayoutPolicyUpdated(previous, _payoutInterval);
    }

    /// @notice Returns the current contract balance.
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }

    /// @notice Returns true when a payout can be triggered according to the
    ///         configured cadence.
    function canTriggerPayout() public view returns (bool) {
        return block.timestamp >= lastPayoutAt + payoutInterval && address(this).balance > 0;
    }

    /// @notice Transfers all escrowed funds to the Lil Footsteps wallet. Anyone
    ///         can call this function once the payout interval has elapsed so the
    ///         process can be automated with off-chain agents such as Chainlink
    ///         Keepers, Gelato, or a simple cron job.
    function triggerPayout() external {
        if (!canTriggerPayout()) {
            if (address(this).balance == 0) revert NothingToPayout();
            revert IntervalNotElapsed();
        }
        uint256 amount = address(this).balance;
        lastPayoutAt = block.timestamp;
        lilFootsteps.transfer(amount);
        emit PayoutExecuted(amount, block.timestamp, msg.sender);
    }

    /// @notice Fallback function to accept donations sent directly to the
    ///         contract address without calling deposit().
    receive() external payable {
        emit Deposit(msg.sender, msg.value, block.timestamp);
    }
}
