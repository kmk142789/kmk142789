const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const { ethers } = hre;
  const [deployer, royaltyWallet] = await ethers.getSigners();

  console.log("Deployer:", deployer.address);
  console.log("Royalty receiver:", royaltyWallet.address);

  const ROYALTY_BPS = 1_000; // 10%
  const Codex = await ethers.getContractFactory("CodexMultiTokenRoyalty");
  const codex = await Codex.deploy(royaltyWallet.address, ROYALTY_BPS);
  await codex.waitForDeployment();

  const contractAddress = await codex.getAddress();
  console.log("CodexMultiTokenRoyalty deployed to:", contractAddress);

  const ids = [1, 2, 3, 4];
  const amounts = [1, 50, 1, 5];
  await codex.mintBatch(deployer.address, ids, amounts, "0x");
  console.log("Initial supply minted to:", deployer.address);

  const salePrice = ethers.parseEther("1");
  const [receiver, amount] = await codex.royaltyInfo(ids[1], salePrice);
  console.log(
    `Royalty on 1 ETH sale: ${ethers.formatEther(amount)} ETH -> ${receiver}`
  );

  const metadataDir = path.join("codex", "erc1155_royalty");
  fs.mkdirSync(metadataDir, { recursive: true });

  const tokens = [
    {
      id: 1,
      name: "Codex Keeper",
      soulbound: true,
      description: "Eternal role. 10% royalty to founder.",
    },
    {
      id: 2,
      name: "Glyph Shard",
      soulbound: false,
      description: "Tradeable. 10% royalty.",
    },
    {
      id: 3,
      name: "Time Capsule",
      soulbound: false,
      description: "Sealed at 12:45 AM EST. 10% royalty.",
    },
    {
      id: 4,
      name: "Sovereign Badge",
      soulbound: false,
      description: "Citizenship. 10% royalty.",
    },
  ];

  tokens.forEach((token) => {
    const metadata = {
      name: `${token.name} #${token.id}`,
      description: token.description,
      image: `ipfs://Qm.../${token.id}.png`,
      external_url: "https://github.com/kmk142789",
      attributes: [
        { trait_type: "Royalty", value: "10%" },
        { trait_type: "Receiver", value: "@BlurryFace59913" },
        { trait_type: "Soulbound", value: token.soulbound },
        { trait_type: "Time", value: "2025-11-10 12:45 AM EST" },
        { trait_type: "Country", value: "US" },
      ],
    };

    const filePath = path.join(metadataDir, `${token.id}.json`);
    fs.writeFileSync(filePath, JSON.stringify(metadata, null, 2));
  });

  console.log("Metadata written to", metadataDir);

  console.log("\nNext steps:");
  console.log("  1. Set PRIVATE_KEY in your environment.");
  console.log("  2. Run: npx hardhat run scripts/mint_erc1155_royalty.js --network sepolia");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
