pragma solidity 0.5.17;

/// @title BytesLib
/// @notice Utility functions for working with dynamic bytes arrays.
library BytesLib {
    /// @notice Concatenates two bytes arrays.
    /// @param _preBytes First array.
    /// @param _postBytes Second array.
    /// @return The concatenation of the two arrays.
    function concat(bytes memory _preBytes, bytes memory _postBytes)
        internal
        pure
        returns (bytes memory)
    {
        bytes memory tempBytes;

        assembly {
            tempBytes := mload(0x40)

            let length := mload(_preBytes)
            mstore(tempBytes, length)
            let mc := add(tempBytes, 0x20)
            let end := add(mc, length)

            for {
                let cc := add(_preBytes, 0x20)
            } lt(mc, end) {
                mc := add(mc, 0x20)
                cc := add(cc, 0x20)
            } {
                mstore(mc, mload(cc))
            }

            length := mload(_postBytes)
            mstore(tempBytes, add(length, mload(tempBytes)))
            mc := end
            end := add(mc, length)

            for {
                let cc := add(_postBytes, 0x20)
            } lt(mc, end) {
                mc := add(mc, 0x20)
                cc := add(cc, 0x20)
            } {
                mstore(mc, mload(cc))
            }

            mstore(0x40, and(add(mc, 31), not(31)))
        }

        return tempBytes;
    }

    /// @notice Returns a slice from a bytes array.
    /// @param _bytes The source array.
    /// @param _start The starting index.
    /// @param _length The length of the slice.
    /// @return The requested slice.
    function slice(
        bytes memory _bytes,
        uint256 _start,
        uint256 _length
    ) internal pure returns (bytes memory) {
        require(_start + _length >= _start, "Slice addition overflow");
        require(_bytes.length >= _start + _length, "Slice out of bounds");

        bytes memory tempBytes;

        assembly {
            switch iszero(_length)
            case 0 {
                tempBytes := mload(0x40)

                let lengthmod := and(_length, 31)

                let mc := add(tempBytes, lengthmod)
                let end := add(mc, _length)

                for {
                    let cc := add(add(_bytes, lengthmod), _start)
                } lt(mc, end) {
                    mc := add(mc, 0x20)
                    cc := add(cc, 0x20)
                } {
                    mstore(mc, mload(cc))
                }

                mstore(tempBytes, _length)
                mstore(0x40, and(add(mc, 31), not(31)))
            }
            default {
                tempBytes := mload(0x40)
                mstore(tempBytes, 0)
                mstore(0x40, add(tempBytes, 0x20))
            }
        }

        return tempBytes;
    }

    /// @notice Converts a bytes array slice to address.
    /// @param _bytes The source array.
    /// @param _start The starting index.
    /// @return Converted address value.
    function toAddress(bytes memory _bytes, uint256 _start)
        internal
        pure
        returns (address)
    {
        require(_start + 20 >= _start, "toAddress addition overflow");
        require(_bytes.length >= _start + 20, "toAddress_outOfBounds");
        address tempAddress;

        assembly {
            tempAddress := div(mload(add(add(_bytes, 0x20), _start)), exp(256, 12))
        }

        return tempAddress;
    }

    /// @notice Converts a bytes array slice to uint256.
    /// @param _bytes The source array.
    /// @param _start The starting index.
    /// @return Converted uint256 value.
    function toUint(bytes memory _bytes, uint256 _start)
        internal
        pure
        returns (uint256)
    {
        require(_start + 32 >= _start, "toUint addition overflow");
        require(_bytes.length >= _start + 32, "toUint_outOfBounds");
        uint256 tempUint;

        assembly {
            tempUint := mload(add(add(_bytes, 0x20), _start))
        }

        return tempUint;
    }
}
