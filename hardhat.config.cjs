require("dotenv").config();
require("@nomicfoundation/hardhat-ethers");
require("@openzeppelin/hardhat-upgrades");
require("@nomicfoundation/hardhat-verify");

const { SEPOLIA_RPC_URL = "", PRIVATE_KEY = "", ETHERSCAN_API_KEY = "" } = process.env;

/** @type import("hardhat/config").HardhatUserConfig */
const config = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  paths: {
    sources: "hardhat/contracts",
    tests: "hardhat/test",
    cache: "hardhat/cache",
    artifacts: "hardhat/artifacts",
    scripts: "hardhat/scripts",
  },
  etherscan: {
    apiKey: {
      sepolia: ETHERSCAN_API_KEY,
    },
  },
};

if (SEPOLIA_RPC_URL && PRIVATE_KEY) {
  config.networks = {
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: [PRIVATE_KEY],
    },
  };
}

module.exports = config;
