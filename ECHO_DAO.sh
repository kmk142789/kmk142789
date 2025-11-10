#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
GLYPH="⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂⟞⟘⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉"

print_banner() {
  echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║   ${GLYPH}  ECHO DAO GOVERNANCE v4.0  ${GLYPH}   ║${NC}"
  echo -e "${CYAN}║        @BlurryFace59913 → kmk142789@github       ║${NC}"
  echo -e "${CYAN}║       November 10, 2025 12:35 AM EST             ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
  echo -e "${PURPLE}${GLYPH}${NC}\n"
}

ensure_contracts_dir() {
  mkdir -p contracts scripts
}

write_contracts() {
  cat <<'TOKEN' > contracts/ECHOToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ECHOToken is ERC20Votes, Ownable {
    constructor()
        ERC20("Echo Governance Token", "ECHO")
        ERC20Permit("Echo")
        Ownable(msg.sender)
    {
        _mint(msg.sender, 1_000_000 * 10 ** 18);
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
TOKEN

  cat <<'GOV' > contracts/EchoGovernor.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";

contract EchoGovernor is
    Governor,
    GovernorSettings,
    GovernorCountingSimple,
    GovernorVotes,
    GovernorVotesQuorumFraction
{
    event GlyphProposal(string description);

    constructor(IVotes _token)
        Governor("EchoDAO")
        GovernorSettings(1, 45818, 0)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4)
    {}

    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    )
        public
        override
        returns (uint256)
    {
        emit GlyphProposal(description);
        return super.propose(targets, values, calldatas, description);
    }
}
GOV

  cat <<'TREASURY' > contracts/EchoTreasury.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

contract EchoTreasury is Ownable {
    event FundsReceived(address sender, uint256 amount);
    event FundsWithdrawn(address to, uint256 amount);

    receive() external payable {
        emit FundsReceived(msg.sender, msg.value);
    }

    function withdraw(address payable to, uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Insufficient funds");
        to.transfer(amount);
        emit FundsWithdrawn(to, amount);
    }
}
TREASURY

  cat <<'SOUL' > contracts/EchoSoulbound.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract EchoSoulbound is ERC721 {
    mapping(uint256 => bool) public isSoulbound;

    constructor() ERC721("Echo Soulbound License", "⿻SOUL") {}

    function mint(address to, uint256 tokenId) external {
        _safeMint(to, tokenId);
        isSoulbound[tokenId] = true;
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override {
        require(from == address(0) || !isSoulbound[tokenId], "Soulbound: non-transferable");
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }
}
SOUL
}

write_deploy_script() {
  cat <<'DEPLOY' > scripts/deploy_dao.js
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
DEPLOY
}

prompt_key_and_deploy() {
  echo -e "${GREEN}Enter PRIVATE KEY to activate DAO:${NC}"
  read -r -p "0x" KEY || true
  export KEY
  echo -e "${PURPLE}DEPLOYING ECHO DAO...${NC}"
  if ! npx hardhat run scripts/deploy_dao.js --network sepolia; then
    echo -e "${RED}Hardhat execution failed. Ensure dependencies, RPC URL, and KEY are configured.${NC}"
    return 1
  fi
}

print_summary() {
  echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║      ${GLYPH}  ECHO DAO IS SOVEREIGN  ${GLYPH}     ║${NC}"
  echo -e "${CYAN}║        @BlurryFace59913 → kmk142789@github       ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
  echo -e "${YELLOW}   • $ECHO Token: 1,000,000${NC}"
  echo -e "${YELLOW}   • Governor: Active${NC}"
  echo -e "${YELLOW}   • Treasury: Owned by DAO${NC}"
  echo -e "${YELLOW}   • Soulbound #001: kmk142789${NC}"
  echo -e "${PURPLE}   • First Proposal: Active${NC}"
  echo -e "${CYAN}   • Next: ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶ → Echo Creates Its Own Laws${NC}"
}

main() {
  print_banner
  ensure_contracts_dir
  write_contracts
  write_deploy_script
  prompt_key_and_deploy || true
  print_summary
}

main "$@"
