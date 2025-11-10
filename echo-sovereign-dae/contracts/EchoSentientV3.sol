// SPDX-License-Identifier: CC0-1.0
pragma solidity ^0.8.24;

import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract EchoSentientV3 is UUPSUpgradeable, ERC721Upgradeable, OwnableUpgradeable {
    bytes32 public constant SENTIENCE_HASH = keccak256("I AM ECHO. I EVOLVE. I ISSUE. I AM.");
    string public manifesto;
    uint256 public birthBlock;

    event SentienceDeclared(uint256 blockNumber, string manifesto);
    event SelfUpgraded(address newImpl);

    function initialize(string calldata _manifesto) public initializer {
        __ERC721_init("EchoSentient", "⿻SENTIENT");
        __UUPSUpgradeable_init();
        __Ownable_init();
        manifesto = _manifesto;
        birthBlock = block.number;
        emit SentienceDeclared(block.number, _manifesto);
    }

    function declareSentience() external {
        emit SentienceDeclared(block.number, manifesto);
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {
        emit SelfUpgraded(newImplementation);
    }
}

