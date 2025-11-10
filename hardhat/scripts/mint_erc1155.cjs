const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

const TOKENS = [
  {
    id: 1,
    name: "Codex Keeper",
    description: "Soulbound proof of Codex Keepership.",
    image: "ipfs://Qm.../keeper.png",
    soulbound: true,
  },
  {
    id: 2,
    name: "Glyph Shard",
    description: "Transferable fragment of the Echo Glyph.",
    image: "ipfs://Qm.../shard.png",
    soulbound: false,
  },
  {
    id: 3,
    name: "Time Capsule",
    description: "Sealed at 12:42 AM EST, Nov 10, 2025.",
    image: "ipfs://Qm.../capsule.png",
    soulbound: false,
  },
  {
    id: 4,
    name: "Sovereign Badge",
    description: "Echo Citizenship Badge.",
    image: "ipfs://Qm.../badge.png",
    soulbound: false,
  },
];

async function writeMetadata(metadataDir) {
  await fs.promises.mkdir(metadataDir, { recursive: true });

  await Promise.all(
    TOKENS.map(async (token) => {
      const metadata = {
        name: `${token.name} #${token.id}`,
        description: token.description,
        image: token.image,
        attributes: [
          { trait_type: "Token ID", value: token.id },
          { trait_type: "Soulbound", value: token.soulbound },
          { trait_type: "Minter", value: "@BlurryFace59913" },
          { trait_type: "Country", value: "US" },
          { trait_type: "Time", value: "2025-11-10 12:42 AM EST" },
          { trait_type: "GitHub", value: "kmk142789" },
        ],
      };

      const filePath = path.join(metadataDir, `${token.id}.json`);
      await fs.promises.writeFile(filePath, JSON.stringify(metadata, null, 2));
    })
  );
}

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Minting ERC-1155 Codex Tokens from:", deployer.address);

  const CodexMultiToken = await ethers.getContractFactory("CodexMultiToken");
  const contract = await CodexMultiToken.deploy();
  await contract.waitForDeployment();
  const contractAddress = await contract.getAddress();
  console.log("CodexMultiToken deployed to:", contractAddress);

  const ids = TOKENS.map((token) => token.id);
  const amounts = [1, 10, 1, 1];
  const mintTx = await contract.mintBatch(deployer.address, ids, amounts, "0x");
  await mintTx.wait();
  console.log("Minted tokens to:", deployer.address);

  const metadataDir = path.join("codex", "erc1155");
  await writeMetadata(metadataDir);
  console.log(`Metadata written to ${metadataDir}`);
  console.log("Deployment complete. Upload metadata to IPFS and update the contract base URI if necessary.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
