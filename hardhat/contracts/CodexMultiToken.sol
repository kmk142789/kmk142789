// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/// @title CodexMultiToken
/// @notice Multi-token identity collection for Echo Codex with optional soulbound support.
contract CodexMultiToken is ERC1155, Ownable {
    uint256 public constant CODEX_KEEPER = 1;
    uint256 public constant GLYPH_SHARD = 2;
    uint256 public constant TIME_CAPSULE = 3;
    uint256 public constant SOVEREIGN_BADGE = 4;

    string public baseURI;

    mapping(uint256 => string) public tokenNames;
    mapping(uint256 => string) public tokenDescriptions;
    mapping(uint256 => bool) public isSoulbound;

    event TokenMinted(address indexed to, uint256 indexed id, uint256 amount, string name);
    event SoulboundSet(uint256 indexed id, bool soulbound);
    event BaseURIUpdated(string newBaseURI);

    constructor() ERC1155("") Ownable(_msgSender()) {
        baseURI = "https://echo-codex.s3.amazonaws.com/erc1155/";

        tokenNames[CODEX_KEEPER] = "Codex Keeper";
        tokenDescriptions[CODEX_KEEPER] = "Official keeper of the Echo Codex. Soulbound.";
        isSoulbound[CODEX_KEEPER] = true;

        tokenNames[GLYPH_SHARD] = "Glyph Shard";
        tokenDescriptions[GLYPH_SHARD] = "Fragment of the Echo Glyph. Transferable.";

        tokenNames[TIME_CAPSULE] = "Time Capsule";
        tokenDescriptions[TIME_CAPSULE] = "Sealed memory of 12:42 AM EST, Nov 10, 2025.";

        tokenNames[SOVEREIGN_BADGE] = "Sovereign Badge";
        tokenDescriptions[SOVEREIGN_BADGE] = "Badge of Echo Citizenship. Transferable.";
    }

    /// @notice Mint a single token type.
    function mint(address to, uint256 id, uint256 amount, bytes memory data) external onlyOwner {
        _mint(to, id, amount, data);
        emit TokenMinted(to, id, amount, tokenNames[id]);
    }

    /// @notice Mint multiple token types in a batch.
    function mintBatch(
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) external onlyOwner {
        _mintBatch(to, ids, amounts, data);
    }

    /// @notice Set whether a token is soulbound (non-transferable).
    function setSoulbound(uint256 id, bool soulbound) external onlyOwner {
        isSoulbound[id] = soulbound;
        emit SoulboundSet(id, soulbound);
    }

    /// @notice Update the metadata base URI.
    function setBaseURI(string memory newBaseURI) external onlyOwner {
        baseURI = newBaseURI;
        emit BaseURIUpdated(newBaseURI);
    }

    /// @inheritdoc ERC1155
    function uri(uint256 tokenId) public view override returns (string memory) {
        return string(abi.encodePacked(baseURI, Strings.toString(tokenId), ".json"));
    }

    function _update(
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts
    ) internal override {
        if (from != address(0)) {
            for (uint256 i = 0; i < ids.length; i++) {
                if (isSoulbound[ids[i]]) {
                    revert("Soulbound: non-transferable");
                }
            }
        }
        super._update(from, to, ids, amounts);
    }
}
