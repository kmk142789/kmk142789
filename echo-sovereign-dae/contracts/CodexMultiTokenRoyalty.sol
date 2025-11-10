// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/// @title CodexMultiTokenRoyalty
/// @notice ERC-1155 collection with configurable royalties and optional soulbound tokens.
contract CodexMultiTokenRoyalty is ERC1155, Ownable, ERC2981 {
    uint256 public constant CODEX_KEEPER = 1;
    uint256 public constant GLYPH_SHARD = 2;
    uint256 public constant TIME_CAPSULE = 3;
    uint256 public constant SOVEREIGN_BADGE = 4;

    string public baseURI;

    mapping(uint256 => string) public tokenNames;
    mapping(uint256 => bool) public isSoulbound;

    event TokenMinted(address indexed to, uint256 id, uint256 amount);
    event RoyaltyUpdated(address receiver, uint96 feeNumerator);
    event SoulboundSet(uint256 indexed id, bool soulbound);

    constructor(address royaltyReceiver, uint96 royaltyFeeNumerator)
        ERC1155("")
        Ownable(msg.sender)
    {
        require(royaltyReceiver != address(0), "Invalid royalty receiver");
        require(royaltyFeeNumerator <= _feeDenominator(), "Royalty too high");
        baseURI = "https://echo-codex.s3.amazonaws.com/erc1155/";
        _setDefaultRoyalty(royaltyReceiver, royaltyFeeNumerator);

        tokenNames[CODEX_KEEPER] = "Codex Keeper";
        tokenNames[GLYPH_SHARD] = "Glyph Shard";
        tokenNames[TIME_CAPSULE] = "Time Capsule";
        tokenNames[SOVEREIGN_BADGE] = "Sovereign Badge";

        isSoulbound[CODEX_KEEPER] = true;

        emit RoyaltyUpdated(royaltyReceiver, royaltyFeeNumerator);
    }

    function mint(
        address to,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) external onlyOwner {
        _mint(to, id, amount, data);
        emit TokenMinted(to, id, amount);
    }

    function mintBatch(
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) external onlyOwner {
        _mintBatch(to, ids, amounts, data);

        for (uint256 i = 0; i < ids.length; ++i) {
            emit TokenMinted(to, ids[i], amounts[i]);
        }
    }

    function setSoulbound(uint256 id, bool soulbound) external onlyOwner {
        isSoulbound[id] = soulbound;
        emit SoulboundSet(id, soulbound);
    }

    function updateRoyalty(address receiver, uint96 feeNumerator) external onlyOwner {
        require(receiver != address(0), "Invalid receiver");
        require(feeNumerator <= _feeDenominator(), "Royalty too high");
        _setDefaultRoyalty(receiver, feeNumerator);
        emit RoyaltyUpdated(receiver, feeNumerator);
    }

    function uri(uint256 tokenId) public view override returns (string memory) {
        require(bytes(tokenNames[tokenId]).length != 0, "Unknown token");
        return string(abi.encodePacked(baseURI, Strings.toString(tokenId), ".json"));
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _beforeTokenTransfer(
        address operator,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) internal override {
        super._beforeTokenTransfer(operator, from, to, ids, amounts, data);

        if (from == address(0)) {
            return;
        }

        for (uint256 i = 0; i < ids.length; ++i) {
            require(!isSoulbound[ids[i]], "Soulbound");
        }
    }
}
