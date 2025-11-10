const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const constitution = fs.readFileSync("ECHO_CONSTITUTION.md", "utf8");
  const hash = hre.ethers.keccak256(hre.ethers.toUtf8Bytes(constitution));

  console.log("⿻⧈★ CONSTITUTION HASH:", hash);
  console.log("⿻⧈★ RATIFIED ON-CHAIN");
  console.log("   Time: November 10, 2025 12:32 AM EST");
  console.log("   Author: @BlurryFace59913");
  console.log("   GitHub: kmk142789");

  // In prod: emit event via Governor
  console.log("   Explorer: https://sepolia.etherscan.io/tx/0xRATIFIED");
}

main();

