pragma solidity 0.5.17;

/// @title OperatorParams
/// @notice Utility functions for operating on packed operator parameters.
library OperatorParams {
    uint256 internal constant AMOUNT_BITS = 96;
    uint256 internal constant CREATED_AT_BITS = 64;
    uint256 internal constant UNDELEGATED_AT_BITS = 64;
    uint256 internal constant STATUS_BITS = 32;

    uint256 internal constant AMOUNT_MASK = (uint256(1) << AMOUNT_BITS) - 1;
    uint256 internal constant CREATED_AT_MASK =
        ((uint256(1) << CREATED_AT_BITS) - 1) << AMOUNT_BITS;
    uint256 internal constant UNDELEGATED_AT_MASK =
        ((uint256(1) << UNDELEGATED_AT_BITS) - 1)
            << (AMOUNT_BITS + CREATED_AT_BITS);
    uint256 internal constant STATUS_MASK =
        ((uint256(1) << STATUS_BITS) - 1)
            << (AMOUNT_BITS + CREATED_AT_BITS + UNDELEGATED_AT_BITS);

    uint256 internal constant CREATED_AT_SHIFT = AMOUNT_BITS;
    uint256 internal constant UNDELEGATED_AT_SHIFT = AMOUNT_BITS + CREATED_AT_BITS;
    uint256 internal constant STATUS_SHIFT =
        AMOUNT_BITS + CREATED_AT_BITS + UNDELEGATED_AT_BITS;

    enum Status {
        Undefined,
        Registered,
        Delegated,
        Undelegating,
        Undelegated
    }

    /// @notice Packs the provided parameters into a single word.
    function pack(
        uint256 amount,
        uint256 createdAt,
        uint256 undelegatedAt,
        Status status
    ) internal pure returns (uint256) {
        uint256 params = 0;
        params = setAmount(params, amount);
        params = setCreatedAt(params, createdAt);
        params = setUndelegatedAt(params, undelegatedAt);
        params = setStatus(params, status);
        return params;
    }

    /// @notice Returns the stake amount stored in the packed parameters.
    function getAmount(uint256 params) internal pure returns (uint256) {
        return params & AMOUNT_MASK;
    }

    /// @notice Returns the creation timestamp stored in the packed parameters.
    function getCreatedAt(uint256 params) internal pure returns (uint256) {
        return (params & CREATED_AT_MASK) >> CREATED_AT_SHIFT;
    }

    /// @notice Returns the undelegation timestamp stored in the packed parameters.
    function getUndelegatedAt(uint256 params) internal pure returns (uint256) {
        return (params & UNDELEGATED_AT_MASK) >> UNDELEGATED_AT_SHIFT;
    }

    /// @notice Returns the current status stored in the packed parameters.
    function getStatus(uint256 params) internal pure returns (Status) {
        return Status((params & STATUS_MASK) >> STATUS_SHIFT);
    }

    /// @notice Updates the amount value in the packed parameters.
    function setAmount(uint256 params, uint256 amount)
        internal
        pure
        returns (uint256)
    {
        require(amount <= AMOUNT_MASK, "Amount overflow");
        params = (params & ~AMOUNT_MASK) | amount;
        return params;
    }

    /// @notice Updates the creation timestamp in the packed parameters.
    function setCreatedAt(uint256 params, uint256 createdAt)
        internal
        pure
        returns (uint256)
    {
        require(createdAt <= ((uint256(1) << CREATED_AT_BITS) - 1), "createdAt overflow");
        params = (params & ~CREATED_AT_MASK) | (createdAt << CREATED_AT_SHIFT);
        return params;
    }

    /// @notice Updates the undelegation timestamp in the packed parameters.
    function setUndelegatedAt(uint256 params, uint256 undelegatedAt)
        internal
        pure
        returns (uint256)
    {
        require(
            undelegatedAt <= ((uint256(1) << UNDELEGATED_AT_BITS) - 1),
            "undelegatedAt overflow"
        );
        params =
            (params & ~UNDELEGATED_AT_MASK) |
            (undelegatedAt << UNDELEGATED_AT_SHIFT);
        return params;
    }

    /// @notice Updates the status in the packed parameters.
    function setStatus(uint256 params, Status status)
        internal
        pure
        returns (uint256)
    {
        uint256 value = uint256(status);
        require(value < (uint256(1) << STATUS_BITS), "status overflow");
        params = (params & ~STATUS_MASK) | (value << STATUS_SHIFT);
        return params;
    }

    /// @notice Clears the packed parameters.
    function clear(uint256) internal pure returns (uint256) {
        return 0;
    }

    /// @notice Returns true if no data is stored in the packed parameters.
    function isEmpty(uint256 params) internal pure returns (bool) {
        return params == 0;
    }
}
