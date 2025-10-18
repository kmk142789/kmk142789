import { sha256 } from "@noble/hashes/sha256";
import { keccak_256 as keccak256 } from "@noble/hashes/sha3";
import { hexToBytes, bytesToHex } from "@noble/hashes/utils";
import * as secp from "@noble/curves/secp256k1";
import bs58check from "bs58check";
import { createHash, randomBytes } from "crypto";
import fs from "fs";
import path from "path";

const HEX_REGEX = /^[0-9a-fA-F]{64}$/;
const BASE58_REGEX = /^[1-9A-HJ-NP-Za-km-z]{51,52}$/;

const NETWORK_PREFIX = {
  mainnet: 0x00,
  testnet: 0x6f,
};

function encodeVarint(value) {
  if (value < 0xfd) return Uint8Array.of(value);
  if (value <= 0xffff) return Uint8Array.of(0xfd, value & 0xff, (value >> 8) & 0xff);
  if (value <= 0xffffffff)
    return Uint8Array.of(
      0xfe,
      value & 0xff,
      (value >> 8) & 0xff,
      (value >> 16) & 0xff,
      (value >> 24) & 0xff
    );
  const buf = Buffer.alloc(9);
  buf[0] = 0xff;
  buf.writeBigUInt64LE(BigInt(value), 1);
  return buf;
}

function bitcoinMessageDigest(message) {
  const messageBytes = new TextEncoder().encode(message);
  const prefix = new TextEncoder().encode("Bitcoin Signed Message:\n");
  const payload = Buffer.concat([
    Buffer.from([prefix.length]),
    Buffer.from(prefix),
    Buffer.from(encodeVarint(messageBytes.length)),
    Buffer.from(messageBytes),
  ]);
  const first = createHash("sha256").update(payload).digest();
  return createHash("sha256").update(first).digest();
}

function bitcoinNetworkPrefix(network) {
  if (!network) return NETWORK_PREFIX.mainnet;
  const normalized = network.toLowerCase();
  if (normalized.startsWith("test") || normalized === "regtest") {
    return NETWORK_PREFIX.testnet;
  }
  return NETWORK_PREFIX.mainnet;
}

function sha256Once(buffer) {
  return createHash("sha256").update(buffer).digest();
}

function computeMerkleRoot(buffers) {
  if (buffers.length === 0) {
    return sha256Once(Buffer.from(""));
  }
  let layer = buffers.map((buf) => sha256Once(buf));
  while (layer.length > 1) {
    const next = [];
    for (let index = 0; index < layer.length; index += 2) {
      const left = layer[index];
      const right = layer[index + 1] ?? left;
      next.push(sha256Once(Buffer.concat([left, right])));
    }
    layer = next;
  }
  return layer[0];
}

function getBitcoinP2PKHAddress(publicKeyBytes, network) {
  const sha = createHash("sha256").update(publicKeyBytes).digest();
  const ripe = createHash("ripemd160").update(sha).digest();
  const prefix = bitcoinNetworkPrefix(network);
  const payload = Buffer.concat([Buffer.from([prefix]), ripe]);
  return bs58check.encode(payload);
}

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

  addKey(inputValue) {
    const parsed = parsePrivateKeyInput(inputValue);
    if (!parsed) {
      return false;
    }

    const { privateKeyHex, metadata } = parsed;

    if (this.keys.some((entry) => entry.privateKey === privateKeyHex)) {
      return false;
    }
    let keyBytes;
    try {
      keyBytes = hexToBytes(privateKeyHex);
    } catch (error) {
      return false;
    }
    if (!secp.secp256k1.utils.isValidPrivateKey(keyBytes)) {
      return false;
    }
    const publicKey = secp.secp256k1.getPublicKey(keyBytes, true);
    const address = this.getEthAddress(publicKey);
    this.keys.push({
      privateKey: privateKeyHex,
      publicKey: bytesToHex(publicKey),
      address,
      ethAddress: address,
      format: metadata.format,
      source: metadata.original,
      network: metadata.network ?? null,
      compressed: metadata.compressed ?? null,
    });
    return true;
  }

  getEthAddress(publicKey) {
    const input = publicKey instanceof Uint8Array ? publicKey : hexToBytes(publicKey);
    const uncompressed = secp.secp256k1.ProjectivePoint.fromHex(input).toRawBytes(false);
    const hash = keccak256(uncompressed.slice(1));
    return `0x${bytesToHex(hash.slice(-20))}`;
  }

  getBitcoinAddress(privateKeyHex, compressed, network) {
    const keyBytes = hexToBytes(privateKeyHex);
    const publicKey = secp.secp256k1.getPublicKey(keyBytes, compressed);
    const address = getBitcoinP2PKHAddress(publicKey, network);
    return { address, publicKeyHex: bytesToHex(publicKey) };
  }

  signMessage(message, repeat = 1) {
    if (this.keys.length === 0) {
      throw new Error("No keys loaded");
    }
    if (typeof message !== "string" || message.length === 0) {
      throw new Error("Message must be a non-empty string");
    }
    const iterations = Number.parseInt(repeat, 10);
    if (!Number.isFinite(iterations) || iterations < 1) {
      throw new Error("Repeat count must be a positive integer");
    }
    const messageBytes = new TextEncoder().encode(message);
    const messageHash = sha256(messageBytes);
    const messageHashHex = bytesToHex(messageHash);
    this.signatures = [];
    for (const key of this.keys) {
      for (let index = 0; index < iterations; index += 1) {
        try {
          const signature = secp.secp256k1.sign(messageHash, hexToBytes(key.privateKey), {
            extraEntropy: randomBytes(32),
          });
          this.signatures.push({
            address: key.address,
            signature: signature.toCompactHex(),
            publicKey: key.publicKey,
            message,
            messageHash: messageHashHex,
            keyFormat: key.format,
            keySource: key.source,
            network: key.network,
            compressed: key.compressed,
            signatureIndex: index + 1,
            signatureCount: iterations,
            createdAt: new Date().toISOString(),
          });
        } catch (error) {
          const prefix = key.privateKey.slice(0, 8);
          console.error(
            `Failed to sign with key ${prefix}... (iteration ${index + 1}/${iterations}): ${error.message}`
          );
        }
      }
    }
    return this.signatures;
  }

  signBitcoinMessage(message, repeat = 1, options = {}) {
    if (this.keys.length === 0) {
      throw new Error("No keys loaded");
    }
    if (typeof message !== "string" || message.length === 0) {
      throw new Error("Message must be a non-empty string");
    }
    const iterations = Number.parseInt(repeat, 10);
    if (!Number.isFinite(iterations) || iterations < 1) {
      throw new Error("Repeat count must be a positive integer");
    }

    const { defaultCompressed = true, network: fallbackNetwork = null } = options;
    const digest = bitcoinMessageDigest(message);
    const digestHex = Buffer.from(digest).toString("hex");

    this.signatures = [];
    for (const key of this.keys) {
      const useCompressed =
        typeof key.compressed === "boolean" ? key.compressed : Boolean(defaultCompressed);
      const network = key.network ?? fallbackNetwork ?? "mainnet";
      const { address, publicKeyHex } = this.getBitcoinAddress(
        key.privateKey,
        useCompressed,
        network
      );
      const privBytes = hexToBytes(key.privateKey);
      for (let index = 0; index < iterations; index += 1) {
        try {
          const signature = secp.secp256k1.sign(digest, privBytes, {
            extraEntropy: randomBytes(32),
          });
          const compact = signature.toCompactRawBytes();
          const recId = signature.recovery ?? 0;
          const header = 27 + recId + (useCompressed ? 4 : 0);
          const raw = new Uint8Array(65);
          raw[0] = header;
          raw.set(compact, 1);
          const rawBuffer = Buffer.from(raw);
          this.signatures.push({
            address,
            network,
            compressed: useCompressed,
            message,
            messageDigest: digestHex,
            signature: rawBuffer.toString("base64"),
            signatureHex: rawBuffer.toString("hex"),
            signatureBytes: rawBuffer,
            header,
            recovery: recId,
            publicKey: publicKeyHex,
            keyFormat: key.format,
            keySource: key.source,
            createdAt: new Date().toISOString(),
            signatureIndex: index + 1,
            signatureCount: iterations,
          });
        } catch (error) {
          const prefix = key.privateKey.slice(0, 8);
          console.error(
            `Failed to sign (bitcoin) with key ${prefix}... (iteration ${index + 1}/${iterations}): ${error.message}`
          );
        }
      }
    }
    return this.signatures;
  }

  saveSignatures(filepath) {
    if (this.signatures.length === 0) {
      throw new Error("No signatures to save");
    }
    const resolved = path.resolve(filepath);
    const sanitized = this.signatures.map((entry) => {
      if (!entry || typeof entry !== "object") {
        return entry;
      }
      const { signatureBytes, ...rest } = entry;
      if (signatureBytes instanceof Buffer || signatureBytes instanceof Uint8Array) {
        return { ...rest, signatureBytesHex: Buffer.from(signatureBytes).toString("hex") };
      }
      return rest;
    });
    fs.writeFileSync(resolved, JSON.stringify(sanitized, null, 2));
    return resolved;
  }
}

function getArgValue(args, flag) {
  const index = args.indexOf(flag);
  if (index === -1) return null;
  return index + 1 < args.length ? args[index + 1] : null;
}
function decodeWif(wif) {
  if (!BASE58_REGEX.test(wif)) {
    throw new Error("Value is not a valid Base58 WIF string");
  }

  let payload;
  try {
    payload = bs58check.decode(wif);
  } catch (error) {
    throw new Error(`Invalid WIF: ${error.message}`);
  }

  if (payload.length !== 33 && payload.length !== 34) {
    throw new Error("Unexpected WIF payload length");
  }

  const version = payload[0];
  let network;
  if (version === 0x80) {
    network = "mainnet";
  } else if (version === 0xef) {
    network = "testnet";
  } else {
    throw new Error(`Unknown WIF network prefix: 0x${version.toString(16)}`);
  }

  let compressed = false;
  let privateKeyBytes;
  if (payload.length === 34 && payload[33] === 0x01) {
    compressed = true;
    privateKeyBytes = payload.slice(1, 33);
  } else if (payload.length === 33) {
    privateKeyBytes = payload.slice(1);
  } else {
    throw new Error("Could not infer compression flag from WIF");
  }

  if (privateKeyBytes.length !== 32) {
    throw new Error("Decoded WIF private key must be 32 bytes");
  }

  return {
    privateKeyHex: bytesToHex(privateKeyBytes),
    network,
    compressed,
  };
}

function parsePrivateKeyInput(rawInput) {
  const trimmed = rawInput.trim();
  if (!trimmed) {
    return null;
  }

  const normalized = normalizeHex(trimmed);
  if (HEX_REGEX.test(normalized)) {
    return {
      privateKeyHex: normalized,
      metadata: {
        format: "hex",
        original: trimmed,
        normalized,
      },
    };
  }

  try {
    const { privateKeyHex, network, compressed } = decodeWif(trimmed);
    return {
      privateKeyHex,
      metadata: {
        format: "wif",
        wif: trimmed,
        original: trimmed,
        network,
        compressed,
      },
    };
  } catch (error) {
    return null;
  }
}

if (import.meta.url === `file://${process.argv[1]}` || import.meta.url === `file://${path.resolve(process.argv[1])}`) {
  const args = process.argv.slice(2);
  const keyFile = getArgValue(args, "--keys");
  const key = getArgValue(args, "--key");
  const messageArg = getArgValue(args, "--message") ?? getArgValue(args, "--msg");
  const messageFile = getArgValue(args, "--message-file");
  const outFile = getArgValue(args, "--out");
  const repeatArg =
    getArgValue(args, "--repeat") ??
    getArgValue(args, "--repetitions") ??
    getArgValue(args, "--count");
  const repeat = repeatArg ? Number.parseInt(repeatArg, 10) : 1;
  if (Number.isNaN(repeat) || repeat < 1) {
    console.error("Repeat count must be a positive integer");
    process.exit(1);
  }

  const bitcoinMode = args.includes("--bitcoin") || args.includes("--btc");
  const preferCompressed = args.includes("--prefer-compressed");
  const preferUncompressed = args.includes("--prefer-uncompressed");
  if (preferCompressed && preferUncompressed) {
    console.error("Cannot use both --prefer-compressed and --prefer-uncompressed");
    process.exit(1);
  }
  const defaultCompressed = preferUncompressed ? false : true;
  const networkOverride = getArgValue(args, "--network");

  if (!keyFile && !key) {
    console.error(
      "Usage: node bulk-key-signer.js --keys path/to/keys.txt --message \"Hello\" [--repeat 5] [--out signatures.json]\n" +
        "        node bulk-key-signer.js --key <hex|wif> --message-file message.txt [--repeat 10] [--out signatures.json]\n" +
        "        node bulk-key-signer.js --keys keys.txt --message \"Hello\" --bitcoin [--out proof.json] [--network mainnet|testnet]"
    );
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
    if (bitcoinMode) {
      const signatures = signer.signBitcoinMessage(message, repeat, {
        defaultCompressed,
        network: networkOverride,
      });
      if (signatures.length === 0) {
        console.error("Signing failed for all keys");
        process.exit(1);
      }
      const merkle = computeMerkleRoot(signatures.map((entry) => entry.signatureBytes));
      const combinedSignature = signatures.map((entry) => entry.signature).join("");
      const payload = {
        mode: "bitcoin",
        message,
        messageDigest: signatures[0]?.messageDigest ?? bitcoinMessageDigest(message).toString("hex"),
        signatureCount: signatures.length,
        combinedSignature,
        merkleRoot: Buffer.from(merkle).toString("hex"),
        signatures: signatures.map(({ signatureBytes, ...rest }) => rest),
      };
      if (outFile) {
        const resolved = path.resolve(outFile);
        fs.writeFileSync(resolved, JSON.stringify(payload, null, 2));
        console.log(`Bitcoin signature batch saved to ${resolved}`);
      } else {
        console.log(JSON.stringify(payload, null, 2));
      }
    } else {
      const signatures = signer.signMessage(message, repeat);
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
    }
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}
