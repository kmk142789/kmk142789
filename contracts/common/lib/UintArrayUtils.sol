// SPDX-License-Identifier: MIT
pragma solidity 0.5.17;

library UintArrayUtils {
    function removeValue(uint256[] storage self, uint256 _value)
        internal
        returns (uint256[] storage)
    {
        uint256 index = 0;
        while (index < self.length) {
            if (_value == self[index]) {
                for (uint256 j = index; j < self.length - 1; j++) {
                    self[j] = self[j + 1];
                }
                self.length--;
            } else {
                index++;
            }
        }
        return self;
    }
}
