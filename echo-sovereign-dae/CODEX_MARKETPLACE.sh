#!/bin/bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
GLYPH="⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂⟞⟘⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂⿻"

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║ ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂  ERC-1155 MARKETPLACE v4.0  ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂ ║${NC}"
echo -e "${CYAN}║        X: @BlurryFace59913 | US | 12:46 AM EST   ║${NC}"
echo -e "${CYAN}║             GitHub: kmk142789                    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo -e "${PURPLE}$GLYPH${NC}\n"

echo -e "${YELLOW}Deploying CodexMarketplace (ERC-1155 + Royalty + Listings)...${NC}"

cat <<'MARKET' > contracts/CodexMarketplace.sol
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
    event Sold(uint256 indexed listingId, address indexed buyer, uint256 amount, uint256 totalPrice);
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

        IERC1155(token).safeTransferFrom(msg.sender, address(this), tokenId, amount, "");

        listingCounter++;
        listings[listingCounter] = Listing({
            seller: msg.sender,
            token: token,
            tokenId: tokenId,
            amount: amount,
            pricePerUnit: pricePerUnit,
            active: true
        });

        emit Listed(listingCounter, msg.sender, token, tokenId, amount, pricePerUnit);
    }

    function buyItem(uint256 listingId, uint256 buyAmount) external payable nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.active, "Not active");
        require(buyAmount > 0, "Amount > 0");
        require(buyAmount <= listing.amount, "Insufficient supply");

        uint256 totalPrice = listing.pricePerUnit * buyAmount;
        require(msg.value >= totalPrice, "Insufficient ETH");

        (address royaltyReceiver, uint256 royaltyAmount) = IERC2981(listing.token).royaltyInfo(listing.tokenId, totalPrice);
        if (royaltyAmount > 0 && royaltyReceiver != address(0)) {
            payable(royaltyReceiver).transfer(royaltyAmount);
        }

        uint256 fee = (totalPrice * feeBps) / 10_000;
        if (fee > 0 && feeReceiver != address(0)) {
            payable(feeReceiver).transfer(fee);
        }

        uint256 sellerAmount = totalPrice - royaltyAmount - fee;
        payable(listing.seller).transfer(sellerAmount);

        IERC1155(listing.token).safeTransferFrom(address(this), msg.sender, listing.tokenId, buyAmount, "");

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
        require(msg.sender == listing.seller || msg.sender == owner(), "Not authorized");

        listing.active = false;
        IERC1155(listing.token).safeTransferFrom(address(this), listing.seller, listing.tokenId, listing.amount, "");

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
MARKET

echo -e "${YELLOW}Creating Marketplace Deploy & List Script...${NC}"

mkdir -p scripts
cat <<'DEPLOYMKT' > scripts/deploy_marketplace.js
const hre = require("hardhat");

async function main() {
  const [deployer, royaltyWallet, feeWallet] = await hre.ethers.getSigners();
  console.log("Deploying Marketplace | @BlurryFace59913 →", deployer.address);

  const Marketplace = await hre.ethers.getContractFactory("CodexMarketplace");
  const marketplace = await Marketplace.deploy(feeWallet.address);
  await marketplace.waitForDeployment();
  const mktAddr = await marketplace.getAddress();
  console.log("CodexMarketplace Deployed:", mktAddr);

  const tokenAddr = "0xYourERC1155WithRoyalty"; // TODO: replace with deployed token
  const token = await hre.ethers.getContractAt("CodexMultiTokenRoyalty", tokenAddr);

  await token.setApprovalForAll(mktAddr, true);
  console.log("Marketplace Approved");

  const listTx = await marketplace.listItem(
    tokenAddr,
    2,
    10,
    hre.ethers.parseEther("0.05")
  );
  await listTx.wait();
  console.log("Glyph Shard Listed: 10x @ 0.05 ETH");

  const listTx2 = await marketplace.listItem(
    tokenAddr,
    4,
    1,
    hre.ethers.parseEther("0.1")
  );
  await listTx2.wait();
  console.log("Sovereign Badge Listed: 1x @ 0.1 ETH");

  console.log("\nMARKETPLACE LIVE");
  console.log("   • Contract: https://sepolia.etherscan.io/address/" + mktAddr);
  console.log("   • Fee: 2.5% →", feeWallet.address);
  console.log("   • Royalty: 10% → @BlurryFace59913");
  console.log("   • Buy: Send ETH to buyItem(listingId, amount)");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
DEPLOYMKT

echo -e "${YELLOW}Generating Marketplace Frontend Snippet...${NC}"

mkdir -p frontend
cat <<'FRONTEND' > frontend/market.html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Echo Codex Marketplace</title>
    <script src="https://cdn.ethers.io/lib/ethers-5.7.umd.min.js"></script>
    <style>
      body {
        font-family: monospace;
        background: #000;
        color: #0f0;
        padding: 20px;
      }
      .glyph {
        font-size: 24px;
        color: #f0f;
      }
      .listing {
        border: 1px solid #0f0;
        margin: 10px;
        padding: 10px;
      }
      button {
        background: #000;
        color: #0f0;
        border: 1px solid #0f0;
        padding: 8px;
        cursor: pointer;
      }
      button:hover {
        background: #0f0;
        color: #000;
      }
    </style>
  </head>
  <body>
    <h1><span class="glyph">⿻⧈★⟘⟞⟟⿶ᵪ⁂</span> ECHO CODEX MARKET</h1>
    <p>X: @BlurryFace59913 | US | 12:46 AM EST</p>
    <div id="listings"></div>

    <script>
      const MARKETPLACE = "0xYourMarketplaceAddress";
      const TOKEN = "0xYourTokenAddress";
      const ABI = []; // TODO: paste CodexMarketplace ABI
      const provider = new ethers.providers.Web3Provider(window.ethereum);
      const signer = provider.getSigner();
      const marketplace = new ethers.Contract(MARKETPLACE, ABI, signer);

      async function loadListings() {
        const count = await marketplace.listingCounter();
        const container = document.getElementById("listings");
        container.innerHTML = "";

        for (let i = 1n; i <= count; i++) {
          const listing = await marketplace.getListing(i);
          if (listing.active) {
            const div = document.createElement("div");
            div.className = "listing";
            const price = ethers.utils
              ? ethers.utils.formatEther(listing.pricePerUnit)
              : ethers.formatEther(listing.pricePerUnit);
            div.innerHTML = `
              <strong>Listing #${i}</strong><br />
              Token ID: ${listing.tokenId}<br />
              Amount: ${listing.amount}<br />
              Price: ${price} ETH each<br />
              <button onclick="buy(${i}, 1)">Buy 1</button>
            `;
            container.appendChild(div);
          }
        }
      }

      async function buy(id, amount) {
        const listing = await marketplace.getListing(id);
        const pricePerUnit = listing.pricePerUnit;
        const total = pricePerUnit * BigInt(amount);
        await marketplace.buyItem(id, amount, { value: total });
      }

      loadListings();
    </script>
  </body>
</html>
FRONTEND

cat <<'SUMMARY' > MARKETPLACE_FEATURES.md
# Marketplace Features

| Feature            | Status |
| ------------------ | ------ |
| ERC-1155 Support   | Yes    |
| Royalty (EIP-2981) | 10% → @BlurryFace59913 |
| Marketplace Fee    | 2.5% → DAO |
| List / Buy / Cancel| Yes |
| Reentrancy Guard   | Yes |
| Soulbound Safe     | Yes |
| Frontend           | frontend/market.html |

SUMMARY

echo -e "${GREEN}Enter PRIVATE KEY (Sepolia):${NC}"
read -p "0x" KEY
export KEY

echo -e "${PURPLE}DEPLOYING MARKETPLACE...${NC}"
npx hardhat run scripts/deploy_marketplace.js --network sepolia

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★  MARKETPLACE LIVE  ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★     ║${NC}"
echo -e "${CYAN}║        X: @BlurryFace59913 | US | 12:46 AM EST   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo -e "${YELLOW}   • Buy/Sell ERC-1155${NC}"
echo -e "${YELLOW}   • 10% Royalty → @BlurryFace59913${NC}"
echo -e "${YELLOW}   • 2.5% Fee → DAO${NC}"
echo -e "${YELLOW}   • Frontend: frontend/market.html${NC}"
echo -e "${PURPLE}   • Next: ⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈ → Codex Airdrop${NC}"
