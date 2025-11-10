// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "@openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IERC2981 {
    function royaltyInfo(uint256 tokenId, uint256 salePrice)
        external
        view
        returns (address receiver, uint256 royaltyAmount);
}

contract CodexMarketplace is ERC1155Holder, Ownable, ReentrancyGuard {
    struct Listing {
        address seller;
        address token;
        uint256 tokenId;
        uint256 amount;
        uint256 pricePerUnit;
        bool active;
    }

    uint256 public listingCounter;
    mapping(uint256 => Listing) public listings;

    uint256 public feeBps = 250; // 2.5% marketplace fee
    address public feeReceiver;

    event Listed(
        uint256 indexed listingId,
        address indexed seller,
        address indexed token,
        uint256 tokenId,
        uint256 amount,
        uint256 price
    );
    event Sold(
        uint256 indexed listingId,
        address indexed buyer,
        uint256 amount,
        uint256 totalPrice
    );
    event Cancelled(uint256 indexed listingId);
    event FeeUpdated(uint256 newFeeBps);
    event FeeReceiverUpdated(address newReceiver);

    constructor(address _feeReceiver) Ownable(msg.sender) {
        feeReceiver = _feeReceiver;
    }

    function listItem(
        address token,
        uint256 tokenId,
        uint256 amount,
        uint256 pricePerUnit
    ) external nonReentrant {
        require(amount > 0, "Amount > 0");
        require(pricePerUnit > 0, "Price > 0");

        IERC1155(token).safeTransferFrom(
            msg.sender,
            address(this),
            tokenId,
            amount,
            ""
        );

        listingCounter++;
        listings[listingCounter] = Listing({
            seller: msg.sender,
            token: token,
            tokenId: tokenId,
            amount: amount,
            pricePerUnit: pricePerUnit,
            active: true
        });

        emit Listed(
            listingCounter,
            msg.sender,
            token,
            tokenId,
            amount,
            pricePerUnit
        );
    }

    function buyItem(uint256 listingId, uint256 buyAmount)
        external
        payable
        nonReentrant
    {
        Listing storage listing = listings[listingId];
        require(listing.active, "Not active");
        require(buyAmount > 0, "Amount > 0");
        require(buyAmount <= listing.amount, "Insufficient supply");

        uint256 totalPrice = listing.pricePerUnit * buyAmount;
        require(msg.value >= totalPrice, "Insufficient ETH");

        (address royaltyReceiver, uint256 royaltyAmount) = IERC2981(listing.token)
            .royaltyInfo(listing.tokenId, totalPrice);
        if (royaltyAmount > 0 && royaltyReceiver != address(0)) {
            payable(royaltyReceiver).transfer(royaltyAmount);
        }

        uint256 fee = (totalPrice * feeBps) / 10_000;
        if (fee > 0 && feeReceiver != address(0)) {
            payable(feeReceiver).transfer(fee);
        }

        uint256 sellerAmount = totalPrice - royaltyAmount - fee;
        payable(listing.seller).transfer(sellerAmount);

        IERC1155(listing.token).safeTransferFrom(
            address(this),
            msg.sender,
            listing.tokenId,
            buyAmount,
            ""
        );

        if (buyAmount == listing.amount) {
            listing.active = false;
        } else {
            listing.amount -= buyAmount;
        }

        if (msg.value > totalPrice) {
            payable(msg.sender).transfer(msg.value - totalPrice);
        }

        emit Sold(listingId, msg.sender, buyAmount, totalPrice);
    }

    function cancelListing(uint256 listingId) external {
        Listing storage listing = listings[listingId];
        require(listing.active, "Not active");
        require(
            msg.sender == listing.seller || msg.sender == owner(),
            "Not authorized"
        );

        listing.active = false;
        IERC1155(listing.token).safeTransferFrom(
            address(this),
            listing.seller,
            listing.tokenId,
            listing.amount,
            ""
        );

        emit Cancelled(listingId);
    }

    function updateFee(uint256 newFeeBps) external onlyOwner {
        require(newFeeBps <= 1_000, "Max 10%");
        feeBps = newFeeBps;
        emit FeeUpdated(newFeeBps);
    }

    function updateFeeReceiver(address newReceiver) external onlyOwner {
        feeReceiver = newReceiver;
        emit FeeReceiverUpdated(newReceiver);
    }

    function getListing(uint256 listingId) external view returns (Listing memory) {
        return listings[listingId];
    }
}
