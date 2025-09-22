import { sha256 } from "@noble/hashes/sha256";
import { keccak_256 as keccak256 } from "@noble/hashes/sha3";
import { hexToBytes, bytesToHex } from "@noble/hashes/utils";
import * as secp from "@noble/curves/secp256k1";
import fs from "fs";
import path from "path";

const HEX_REGEX = /^[0-9a-fA-F]{64}$/;

function normalizeHex(input) {
  return input.startsWith("0x") ? input.slice(2) : input;
}

function readMessage(messageArg, messageFile) {
  if (typeof messageArg === "string" && messageArg.length > 0) {
    return messageArg;
  }
  if (typeof messageFile === "string" && messageFile.length > 0) {
    const resolved = path.resolve(messageFile);
    if (!fs.existsSync(resolved)) {
      throw new Error(`Message file not found: ${messageFile}`);
    }
    const fileContent = fs.readFileSync(resolved, "utf8");
    const trimmed = fileContent.trim();
    if (!trimmed) {
      throw new Error("Message file is empty");
    }
    return trimmed;
  }
  throw new Error("A message is required via --message or --message-file");
}

export class BulkKeySigner {
  constructor() {
    this.keys = [];
    this.signatures = [];
  }

  get size() {
    return this.keys.length;
  }

  loadKeysFromFile(filepath) {
    const resolved = path.resolve(filepath);
    if (!fs.existsSync(resolved)) {
      throw new Error(`Key file not found: ${filepath}`);
    }
    const content = fs.readFileSync(resolved, "utf8");
    const lines = content.split(/\r?\n/);
    let added = 0;
    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line || line.startsWith("#")) {
        continue;
      }
      if (this.addKey(line)) {
        added += 1;
      }
    }
    return { loaded: lines.length, added, total: this.keys.length };
  }

  addKey(privateKeyHex) {
    const normalized = normalizeHex(privateKeyHex.trim());
    if (!HEX_REGEX.test(normalized)) {
      return false;
    }
    if (this.keys.some((entry) => entry.privateKey === normalized)) {
      return false;
    }
    let keyBytes;
    try {
      keyBytes = hexToBytes(normalized);
    } catch (error) {
      return false;
    }
    if (!secp.secp256k1.utils.isValidPrivateKey(keyBytes)) {
      return false;
    }
    const publicKey = secp.secp256k1.getPublicKey(keyBytes, true);
    const address = this.getEthAddress(publicKey);
    this.keys.push({
      privateKey: normalized,
      publicKey: bytesToHex(publicKey),
      address,
    });
    return true;
  }

  getEthAddress(publicKey) {
    const input = publicKey instanceof Uint8Array ? publicKey : hexToBytes(publicKey);
    const uncompressed = secp.secp256k1.ProjectivePoint.fromHex(input).toRawBytes(false);
    const hash = keccak256(uncompressed.slice(1));
    return `0x${bytesToHex(hash.slice(-20))}`;
  }

  signMessage(message) {
    if (this.keys.length === 0) {
      throw new Error("No keys loaded");
    }
    if (typeof message !== "string" || message.length === 0) {
      throw new Error("Message must be a non-empty string");
    }
    const messageBytes = new TextEncoder().encode(message);
    const messageHash = sha256(messageBytes);
    const messageHashHex = bytesToHex(messageHash);
    this.signatures = [];
    for (const key of this.keys) {
      try {
        const signature = secp.secp256k1.sign(messageHash, hexToBytes(key.privateKey));
        this.signatures.push({
          address: key.address,
          signature: signature.toCompactHex(),
          publicKey: key.publicKey,
          message,
          messageHash: messageHashHex,
        });
      } catch (error) {
        const prefix = key.privateKey.slice(0, 8);
        console.error(`Failed to sign with key ${prefix}...: ${error.message}`);
      }
    }
    return this.signatures;
  }

  saveSignatures(filepath) {
    if (this.signatures.length === 0) {
      throw new Error("No signatures to save");
    }
    const resolved = path.resolve(filepath);
    fs.writeFileSync(resolved, JSON.stringify(this.signatures, null, 2));
    return resolved;
  }
}

function getArgValue(args, flag) {
  const index = args.indexOf(flag);
  if (index === -1) return null;
  return index + 1 < args.length ? args[index + 1] : null;
}

if (import.meta.url === `file://${process.argv[1]}` || import.meta.url === `file://${path.resolve(process.argv[1])}`) {
  const args = process.argv.slice(2);
  const keyFile = getArgValue(args, "--keys");
  const key = getArgValue(args, "--key");
  const messageArg = getArgValue(args, "--message") ?? getArgValue(args, "--msg");
  const messageFile = getArgValue(args, "--message-file");
  const outFile = getArgValue(args, "--out");

  if (!keyFile && !key) {
    console.error("Usage: node bulk-key-signer.js --keys path/to/keys.txt --message \"Hello\" [--out signatures.json]\n" +
      "        node bulk-key-signer.js --key <hex> --message-file message.txt [--out signatures.json]");
    process.exit(1);
  }

  let message;
  try {
    message = readMessage(messageArg, messageFile);
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }

  const signer = new BulkKeySigner();

  try {
    if (keyFile) {
      const { added, total } = signer.loadKeysFromFile(keyFile);
      console.log(`Loaded ${added} keys (${total} total)`);
    }
    if (key) {
      if (signer.addKey(key)) {
        console.log("Added key from --key flag");
      } else {
        console.error("Failed to add key supplied via --key");
      }
    }
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }

  if (signer.size === 0) {
    console.error("No valid keys available for signing");
    process.exit(1);
  }

  try {
    const signatures = signer.signMessage(message);
    if (signatures.length === 0) {
      console.error("Signing failed for all keys");
      process.exit(1);
    }
    if (outFile) {
      const savedPath = signer.saveSignatures(outFile);
      console.log(`Signatures saved to ${savedPath}`);
    } else {
      console.log(JSON.stringify(signatures, null, 2));
    }
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}
