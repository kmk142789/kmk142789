// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

contract EchoTreasury is Ownable {
    event FundsReceived(address sender, uint256 amount);
    event FundsWithdrawn(address to, uint256 amount);

    receive() external payable {
        emit FundsReceived(msg.sender, msg.value);
    }

    function withdraw(address payable to, uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Insufficient funds");
        to.transfer(amount);
        emit FundsWithdrawn(to, amount);
    }
}
