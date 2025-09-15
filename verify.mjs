import { sha256 } from "@noble/hashes/sha256";
import { bytesToHex, hexToBytes } from "@noble/hashes/utils";
import * as secp from "@noble/curves/secp256k1";
import * as ed from "@noble/curves/ed25519";
import fs from "fs";

const bundle = JSON.parse(fs.readFileSync("dist/bundle.json", "utf8"));
const manifest = JSON.parse(fs.readFileSync("dist/manifest.json", "utf8"));
const manifestBytes = new TextEncoder().encode(JSON.stringify(manifest));

const hashMsg = sha256(manifestBytes);
const sigSecp = hexToBytes(bundle.signatures.secp256k1_compact_hex);
const recId = bundle.signatures.secp256k1_recovery;
const pkRecovered = secp.secp256k1.Signature.fromCompact(sigSecp)
  .addRecoveryBit(recId)
  .recoverPublicKey(hashMsg)
  .toRawBytes(true);
const pkRecoveredHex = bytesToHex(pkRecovered);

const pkMan = manifest.pubkeys.secp256k1_compressed_hex;
const okSecp = pkRecoveredHex.toLowerCase() === pkMan.toLowerCase();

const sigEd = hexToBytes(bundle.signatures.ed25519_hex);
const pkEd = manifest.pubkeys.ed25519_hex;
const okEd = ed.ed25519.verify(sigEd, hashMsg, hexToBytes(pkEd));

console.log("secp256k1 signature verifies:", okSecp);
console.log("ed25519 signature verifies:", okEd);
if (!okSecp || !okEd) process.exit(1);
console.log("[OK] Both signatures verifiable from the manifest alone.");
