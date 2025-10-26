#!/usr/bin/env node
import { issueCredential } from "@spruceid/didkit-wasm-node";
import crypto from "crypto";
import fs from "fs";

const [donorDid, amount, txHash, fiscalYear] = process.argv.slice(2);
if (!donorDid || !amount || !txHash || !fiscalYear) {
  console.error("Usage: node scripts/issueDonorCredential.mjs <donorDid> <amount> <txHash> <fiscalYear>");
  process.exit(1);
}

const issuerDid = process.env.NONPROFIT_TREASURY_ISSUER_DID;
if (!issuerDid) {
  console.error("Set NONPROFIT_TREASURY_ISSUER_DID to the issuing DID");
  process.exit(1);
}

const keyPath = process.env.NONPROFIT_TREASURY_ISSUER_KEY || "issuerKey.json";
if (!fs.existsSync(keyPath)) {
  console.error(`Issuer key file not found at ${keyPath}`);
  process.exit(1);
}

const key = JSON.parse(fs.readFileSync(keyPath, "utf8"));

const credential = {
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org",
    "https://w3id.org/security/suites/jcs-2021/v1"
  ],
  id: `urn:uuid:${crypto.randomUUID()}`,
  type: ["VerifiableCredential", "NonprofitDonorCredential"],
  issuer: issuerDid,
  issuanceDate: new Date().toISOString(),
  credentialSubject: {
    id: donorDid,
    donation: {
      token: "USDC",
      amount,
      txHash
    },
    fiscalYear
  }
};

const options = {
  proofPurpose: "assertionMethod",
  verificationMethod: `${issuerDid}#controller`,
  proofFormat: "jwt"
};

try {
  const jwt = await issueCredential(
    JSON.stringify(credential),
    JSON.stringify(options),
    JSON.stringify(key)
  );
  console.log("VC (JWT):", jwt);
} catch (error) {
  console.error("Failed to issue credential:", error.message);
  process.exit(1);
}
