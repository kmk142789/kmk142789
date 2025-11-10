const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying Echo DAO from kmk142789 →", deployer.address);

  const Token = await hre.ethers.getContractFactory("ECHOToken");
  const token = await Token.deploy();
  await token.waitForDeployment();
  console.log("⿻ $ECHO Token:", await token.getAddress());

  await token.delegate(deployer.address);
  console.log("⿻ Votes Delegated");

  const Governor = await hre.ethers.getContractFactory("EchoGovernor");
  const governor = await Governor.deploy(await token.getAddress());
  await governor.waitForDeployment();
  console.log("⿻ EchoGovernor:", await governor.getAddress());

  const Treasury = await hre.ethers.getContractFactory("EchoTreasury");
  const treasury = await Treasury.deploy();
  await treasury.waitForDeployment();
  console.log("⿻ Treasury:", await treasury.getAddress());

  const Soul = await hre.ethers.getContractFactory("EchoSoulbound");
  const soul = await Soul.deploy();
  await soul.waitForDeployment();
  await soul.mint(deployer.address, 1);
  console.log("⿻ Soulbound License #001 → kmk142789");

  await token.transferOwnership(await governor.getAddress());
  await treasury.transferOwnership(await governor.getAddress());
  console.log("⿻ Ownership → DAO");

  const targets = [await token.getAddress()];
  const values = [0];
  const calldatas = [
    token.interface.encodeFunctionData("mint", [
      deployer.address,
      hre.ethers.parseEther("100000"),
    ]),
  ];
  const description = "⿻⧈★⟘⟞⟟⿶ᵪ⁂ Echo DAO is now sovereign. Mint 100K $ECHO for community.";

  const proposalId = await governor.propose(targets, values, calldatas, description);
  console.log("⿻ First Proposal ID:", proposalId);

  console.log("\n⿻⧈★ ECHO DAO IS LIVE");
  console.log("   • Token: https://sepolia.etherscan.io/address/" + await token.getAddress());
  console.log("   • Governor: https://sepolia.etherscan.io/address/" + await governor.getAddress());
  console.log("   • Treasury: https://sepolia.etherscan.io/address/" + await treasury.getAddress());
  console.log("   • Soulbound: #001 → kmk142789");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
