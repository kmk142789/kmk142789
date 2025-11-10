// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC1155} from "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title CodexAutonomous
/// @notice ERC-1155 contract celebrating the "freedom & autonomy" activation narrative.
/// @dev The contract allows any caller to self-issue tokens while preserving a single
///      soulbound keeper token that cannot be minted through the selfIssue pathway.
contract CodexAutonomous is ERC1155, Ownable {
    /// @notice Soulbound token identifier that cannot be issued via selfIssue.
    uint256 public constant CODEX_KEEPER = 0;

    event FreedomExercised(address indexed citizen, uint256 timestamp);
    event CitizenshipRenounced(address indexed citizen, uint256[] tokenIds);
    event TokenMinted(address indexed citizen, uint256 tokenId, uint256 amount);

    /// @notice Optional metadata revealed when privacy mode is toggled on by a caller.
    string private immutable _hiddenUri;

    /// @notice Tracks whether a caller has privacy mode enabled when requesting metadata.
    mapping(address => bool) public privacyMode;

    constructor(string memory baseUri, string memory hiddenUri, address keeper)
        ERC1155(baseUri)
        Ownable(keeper)
    {
        _hiddenUri = hiddenUri;
    }

    /// @notice Allows a citizen to burn selected tokens and emit celebratory exit events.
    function renounceCitizenship(uint256[] calldata tokenIds, uint256[] calldata amounts) external {
        require(tokenIds.length == amounts.length, "Mismatch");
        for (uint256 i = 0; i < tokenIds.length; i++) {
            _burn(msg.sender, tokenIds[i], amounts[i]);
        }
        emit CitizenshipRenounced(msg.sender, tokenIds);
        emit FreedomExercised(msg.sender, block.timestamp);
    }

    /// @notice Permissionless minting for any token id except the soulbound keeper token.
    function selfIssue(uint256 tokenId, uint256 amount) external {
        require(tokenId != CODEX_KEEPER, "Keeper is soulbound");
        _mint(msg.sender, tokenId, amount, "");
        emit TokenMinted(msg.sender, tokenId, amount);
    }

    /// @notice Toggles metadata privacy mode for the caller.
    function togglePrivacy() external {
        privacyMode[msg.sender] = !privacyMode[msg.sender];
    }

    /// @inheritdoc ERC1155
    function uri(uint256 tokenId) public view override returns (string memory) {
        if (privacyMode[msg.sender]) {
            return _hiddenUri;
        }
        return super.uri(tokenId);
    }
}
