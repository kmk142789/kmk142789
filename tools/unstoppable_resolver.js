#!/usr/bin/env node
import UD from "@unstoppabledomains/resolution";
import fs from "fs";

const args = process.argv.slice(2);

function printUsage() {
  console.log(
    [
      "Usage:",
      "  node tools/unstoppable_resolver.js <domain> [--ticker SYMBOL] [--chain CHAIN] [--json output.json]",
      "",
      "Examples:",
      "  node tools/unstoppable_resolver.js udtestdev-usdt.crypto --ticker USDT --chain ERC20",
      "  node tools/unstoppable_resolver.js satoshi.nft --ticker ETH",
      "",
      "When a chain is provided the script queries multiChainAddr (e.g. ERC20, MATIC).",
      "Without a chain it queries the standard addr record.",
      "Set UNSTOPPABLE_DOMAINS_API_KEY (or UNSTOPPABLE_API_KEY) to use a proxy API key.",
      "Optional: UNSTOPPABLE_UNS_URL / UNSTOPPABLE_ZNS_URL override default RPC endpoints.",
    ].join("\n")
  );
}

if (args.includes("--help") || args.includes("-h")) {
  printUsage();
  process.exit(0);
}

const positional = args.filter((item) => !item.startsWith("--"));
const domain = positional[0];

function getFlagValue(flag) {
  const index = args.indexOf(flag);
  if (index === -1 || index + 1 >= args.length) {
    return null;
  }
  const value = args[index + 1];
  if (value.startsWith("--")) {
    return null;
  }
  return value;
}

const ticker = getFlagValue("--ticker") || "ETH";
const chain = getFlagValue("--chain");
const jsonOut = getFlagValue("--json");

if (!domain) {
  console.error("Error: a domain is required.");
  printUsage();
  process.exit(1);
}

async function resolveDomain() {
  const { Resolution } = UD;
  if (typeof Resolution !== "function") {
    console.error("@unstoppabledomains/resolution did not expose a Resolution constructor");
    process.exit(1);
  }
  const options = {};
  const apiKey =
    process.env.UNSTOPPABLE_DOMAINS_API_KEY || process.env.UNSTOPPABLE_API_KEY || null;
  if (apiKey) {
    options.apiKey = apiKey;
  }

  const sourceConfig = {};
  const unsUrl = process.env.UNSTOPPABLE_UNS_URL;
  if (unsUrl) {
    sourceConfig.uns = {
      url: unsUrl,
      network: process.env.UNSTOPPABLE_UNS_NETWORK || "mainnet",
    };
  }
  const znsUrl = process.env.UNSTOPPABLE_ZNS_URL;
  if (znsUrl) {
    sourceConfig.zns = {
      url: znsUrl,
      network: process.env.UNSTOPPABLE_ZNS_NETWORK || "mainnet",
    };
  }
  if (Object.keys(sourceConfig).length > 0) {
    options.sourceConfig = sourceConfig;
  }

  const resolution = new Resolution(options);
  try {
    const lookup = chain
      ? await resolution.multiChainAddr(domain, ticker, chain)
      : await resolution.addr(domain, ticker);
    const result = {
      domain,
      ticker,
      chain: chain || null,
      address: lookup,
    };

    if (jsonOut) {
      fs.writeFileSync(jsonOut, `${JSON.stringify(result, null, 2)}\n`);
      console.log(`Saved result to ${jsonOut}`);
    } else {
      console.log(JSON.stringify(result, null, 2));
    }
  } catch (error) {
    console.error(`Failed to resolve ${domain}: ${error.message}`);
    process.exitCode = 1;
  }
}

resolveDomain();
