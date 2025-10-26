// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title NonprofitTreasury
/// @notice Collects ERC-20 donations and releases funds to the Little Footsteps
///         multisig when authorized by the treasurer role.
/// @dev    The contract mirrors the off-chain NonprofitBank process while
///         supporting stablecoins and granular donor attribution. It implements
///         a minimal role-based access control layer so auditors can verify
///         administrator changes on-chain.
contract NonprofitTreasury {
    /// @notice Lightweight ERC-20 interface used by the treasury.
    interface IERC20 {
        function transfer(address recipient, uint256 amount) external returns (bool);

        function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

        function balanceOf(address account) external view returns (uint256);
    }

    /// @notice Emitted whenever a donor contributes funds to the treasury.
    event DonationReceived(address indexed donor, uint256 amount, string memo);

    /// @notice Emitted whenever the treasurer disburses funds to the beneficiary.
    event DisbursementExecuted(address indexed beneficiary, uint256 amount, string reason);

    /// @notice Emitted when a role assignment changes.
    event RoleGranted(bytes32 indexed role, address indexed account, address indexed sender);

    /// @notice Emitted when a role is revoked from an account.
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed sender);

    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;
    bytes32 public constant TREASURER_ROLE = keccak256("TREASURER_ROLE");

    /// @dev Guard states for the nonReentrant modifier.
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status;

    address public beneficiary;
    IERC20 public immutable stablecoin;

    uint256 public totalDonations;
    uint256 public totalDisbursed;

    struct DonationMetadata {
        uint256 amount;
        uint256 timestamp;
        address donor;
    }

    DonationMetadata[] public donationLog;

    mapping(bytes32 => mapping(address => bool)) private _roles;

    modifier nonReentrant() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }

    modifier onlyRole(bytes32 role) {
        require(hasRole(role, msg.sender), "AccessControl: missing role");
        _;
    }

    constructor(address stablecoinAddress, address beneficiaryWallet, address admin) {
        require(stablecoinAddress != address(0), "Treasury: invalid token");
        require(beneficiaryWallet != address(0), "Treasury: invalid beneficiary");
        require(admin != address(0), "Treasury: invalid admin");

        stablecoin = IERC20(stablecoinAddress);
        beneficiary = beneficiaryWallet;
        _status = _NOT_ENTERED;

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(TREASURER_ROLE, admin);
    }

    /// @notice Transfers funds from the donor into the treasury and records the metadata.
    /// @param amount The number of tokens to transfer (USDC uses 6 decimals).
    /// @param memo Optional donor supplied memo for attribution.
    function donate(uint256 amount, string calldata memo) external nonReentrant {
        require(amount > 0, "Treasury: amount must be > 0");
        require(stablecoin.transferFrom(msg.sender, address(this), amount), "Treasury: transfer failed");

        totalDonations += amount;
        donationLog.push(DonationMetadata({amount: amount, timestamp: block.timestamp, donor: msg.sender}));
        emit DonationReceived(msg.sender, amount, memo);
    }

    /// @notice Releases tokens to the beneficiary wallet when the treasurer authorizes it.
    /// @param amount The number of tokens to release.
    /// @param reason Explanation recorded on-chain for transparency.
    function disburse(uint256 amount, string calldata reason) external onlyRole(TREASURER_ROLE) nonReentrant {
        require(amount > 0, "Treasury: amount must be > 0");
        require(amount <= stablecoin.balanceOf(address(this)), "Treasury: insufficient balance");

        totalDisbursed += amount;
        require(stablecoin.transfer(beneficiary, amount), "Treasury: disbursement failed");

        emit DisbursementExecuted(beneficiary, amount, reason);
    }

    /// @notice Updates the payout destination. Restricted to the default admin.
    function setBeneficiary(address newBeneficiary) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newBeneficiary != address(0), "Treasury: invalid beneficiary");
        beneficiary = newBeneficiary;
    }

    /// @notice Returns the number of donations recorded by the contract.
    function getDonationCount() external view returns (uint256) {
        return donationLog.length;
    }

    /// @notice Returns true if the account has been assigned the provided role.
    function hasRole(bytes32 role, address account) public view returns (bool) {
        return _roles[role][account];
    }

    /// @notice Grants a role to the specified account. Only callable by the admin role.
    function grantRole(bytes32 role, address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _grantRole(role, account);
    }

    /// @notice Revokes a role from the specified account. Only callable by the admin role.
    function revokeRole(bytes32 role, address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_roles[role][account]) {
            _roles[role][account] = false;
            emit RoleRevoked(role, account, msg.sender);
        }
    }

    function _grantRole(bytes32 role, address account) internal {
        require(account != address(0), "Treasury: invalid role account");
        if (!_roles[role][account]) {
            _roles[role][account] = true;
            emit RoleGranted(role, account, msg.sender);
        }
    }
}
