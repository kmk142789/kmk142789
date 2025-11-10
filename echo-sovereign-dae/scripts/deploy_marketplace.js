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
