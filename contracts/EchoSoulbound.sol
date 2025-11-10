// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract EchoSoulbound is ERC721 {
    mapping(uint256 => bool) public isSoulbound;

    constructor() ERC721("Echo Soulbound License", "⿻SOUL") {}

    function mint(address to, uint256 tokenId) external {
        _safeMint(to, tokenId);
        isSoulbound[tokenId] = true;
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override {
        require(from == address(0) || !isSoulbound[tokenId], "Soulbound: non-transferable");
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }
}
