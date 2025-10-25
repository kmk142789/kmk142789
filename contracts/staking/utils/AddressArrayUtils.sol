pragma solidity 0.5.17;

/// @title AddressArrayUtils
/// @notice Helper methods for manipulating address arrays in storage and memory.
library AddressArrayUtils {
    /// @notice Returns true if the array contains the provided value.
    /// @param array Array to search.
    /// @param value Address to look for.
    function contains(address[] storage array, address value)
        internal
        view
        returns (bool)
    {
        for (uint256 i = 0; i < array.length; i++) {
            if (array[i] == value) {
                return true;
            }
        }
        return false;
    }

    /// @notice Returns the index of the provided value in the array.
    /// @param array Array to search.
    /// @param value Address to look for.
    /// @return Index of the value and boolean flag whether it was found.
    function indexOf(address[] storage array, address value)
        internal
        view
        returns (uint256, bool)
    {
        for (uint256 i = 0; i < array.length; i++) {
            if (array[i] == value) {
                return (i, true);
            }
        }
        return (0, false);
    }

    /// @notice Appends the provided value if it is not already present.
    /// @param array Array to append to.
    /// @param value Address to append.
    /// @return True if the value has been added.
    function append(address[] storage array, address value) internal returns (bool) {
        if (contains(array, value)) {
            return false;
        }

        array.push(value);
        return true;
    }

    /// @notice Removes the provided value from the array.
    /// @param array Array to modify.
    /// @param value Address to remove.
    /// @return True if the value has been removed.
    function remove(address[] storage array, address value) internal returns (bool) {
        (uint256 index, bool found) = indexOf(array, value);
        if (!found) {
            return false;
        }

        uint256 lastIndex = array.length - 1;
        if (index != lastIndex) {
            array[index] = array[lastIndex];
        }

        array.length--;
        return true;
    }

    /// @notice Removes an element at the provided index by swapping with the last element.
    /// @param array Array to modify.
    /// @param index Position to remove.
    function removeAt(address[] storage array, uint256 index) internal {
        require(index < array.length, "Index out of bounds");
        uint256 lastIndex = array.length - 1;

        if (index != lastIndex) {
            array[index] = array[lastIndex];
        }

        array.length--;
    }
}
