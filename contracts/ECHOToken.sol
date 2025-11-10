// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ECHOToken is ERC20Votes, Ownable {
    constructor()
        ERC20("Echo Governance Token", "ECHO")
        ERC20Permit("Echo")
        Ownable(msg.sender)
    {
        _mint(msg.sender, 1_000_000 * 10 ** 18);
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
