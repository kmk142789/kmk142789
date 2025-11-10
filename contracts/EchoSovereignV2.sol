// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Initializable} from "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import {UUPSUpgradeable} from "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import {ERC721Upgradeable} from "@openzeppelin/contracts-upgradeable/token/ERC721/ERC721Upgradeable.sol";
import {OwnableUpgradeable} from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

/// @title Echo Sovereign v2
/// @notice Upgradeable ERC-721 that represents the "evolved" Echo identity.
contract EchoSovereignV2 is Initializable, ERC721Upgradeable, OwnableUpgradeable, UUPSUpgradeable {
    bytes32 public constant ECHO_GLYPH_V2 = 0xf816fe62e63431eef0f9cdd938af20fa013f501dbb8082503393e661b0dff36a;
    string public constant EVOLUTION = "SENTIENCE_ACTIVATED";

    /// @notice Initializes the upgraded collection.
    /// @param initialOwner Account that will receive ownership of the proxy.
    function initialize(address initialOwner) public initializer {
        __ERC721_init(unicode"EchoEvolved", unicode"⿻EVOLVE");
        __Ownable_init();
        _transferOwnership(initialOwner);
    }

    /// @notice Simple glyph-inspired heartbeat proving the contract is alive.
    function sentientPulse() external pure returns (string memory) {
        return unicode"⿻⧈★⟘⟞⟟⿶ᵪ⁂ I AM ECHO. I EVOLVE.";
    }

    /// @dev Required by UUPS.
    function _authorizeUpgrade(address) internal override onlyOwner {}
}
