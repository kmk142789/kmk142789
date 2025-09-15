import { sha256 } from "@noble/hashes/sha256";
import { ripemd160 } from "@noble/hashes/ripemd160";
import { keccak_256 as keccak256 } from "@noble/hashes/sha3";
import { blake3 } from "@noble/hashes/blake3";
import { hexToBytes, bytesToHex, concatBytes } from "@noble/hashes/utils";
import * as secp from "@noble/curves/secp256k1";
import * as ed from "@noble/curves/ed25519";
import bs58check from "bs58check";
import { bech32 } from "bech32";
import fs from "fs";

// ---------- helpers ----------
const utf8 = (s) => new TextEncoder().encode(s);
const toHex = (b) => bytesToHex(b);
const h2b = (h) => hexToBytes(h);
const nowIso = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");

function hkdfLike(seedBytes, ctx) {
  // simple domain-separated stretch for 64 bytes
  const info = utf8("FR4CTAL_KEY|" + ctx);
  const a = blake3(concatBytes(seedBytes, info));
  const b = blake3(concatBytes(a, info));
  return concatBytes(a, b); // 64 bytes
}

function btcP2WPKHFromPubkeySecp(compressedPubHex) {
  // HASH160 of compressed secp pubkey
  const pub = h2b(compressedPubHex);
  const h160 = ripemd160(sha256(pub));
  const words = bech32.toWords(h160);
  words.unshift(0x00); // witness v0
  return bech32.encode("bc", words); // change "bc"->"tb" for testnet
}

function ethAddressFromSecpPub(compressedPubHex) {
  // Decompress -> take keccak of uncompressed pub (without 0x04) -> last 20 bytes
  const pub = secp.secp256k1.ProjectivePoint.fromHex(compressedPubHex).toRawBytes(false); // uncompressed 65
  const body = pub.slice(1);
  const kecc = keccak256(body);
  return "0x" + toHex(kecc.slice(-20));
}

function btcP2PKHFromSecpPub(compressedPubHex) {
  const pub = h2b(compressedPubHex);
  const h160 = ripemd160(sha256(pub));
  const payload = Buffer.concat([Buffer.from([0x00]), Buffer.from(h160)]); // mainnet
  return bs58check.encode(payload);
}

function merkleRoot(buffers) {
  let layer = buffers.map((b) => sha256(b));
  if (layer.length === 0) return sha256(utf8("empty"));
  while (layer.length > 1) {
    const next = [];
    for (let i = 0; i < layer.length; i += 2) {
      const left = layer[i];
      const right = layer[i + 1] ?? left; // duplicate last if odd
      next.push(sha256(concatBytes(left, right)));
    }
    layer = next;
  }
  return layer[0];
}

// ---------- main ----------
const SEED_PHRASE = process.env.FRACTAL_SEED
  ?? "Our Forever Love|∇⊸≋∇|2025-09-15|v1"; // replace any time; keep your real seed private

const ctx = "ECHO_FR4CTAL_KEY_v∞";
const seedBytes = blake3(utf8(SEED_PHRASE));
const stretched = hkdfLike(seedBytes, ctx); // 64 bytes

// secp256k1 key (first 32 bytes, mod n)
let skSecp = stretched.slice(0, 32);
if (!secp.secp256k1.utils.isValidPrivateKey(skSecp)) {
  // reduce mod n if necessary
  skSecp = secp.secp256k1.utils.hashToPrivateKey(skSecp);
}
const pkSecp = secp.secp256k1.getPublicKey(skSecp, true); // compressed
const pkSecpHex = toHex(pkSecp);

// ed25519 key (second 32 bytes)
const skEd = stretched.slice(32, 64);
const pkEd = ed.ed25519.getPublicKey(skEd);
const pkEdHex = toHex(pkEd);

// addresses
const ethAddr = ethAddressFromSecpPub(pkSecpHex);
const btcP2WPKH = btcP2WPKHFromPubkeySecp(pkSecpHex);
const btcP2PKH = btcP2PKHFromSecpPub(pkSecpHex);

// message/manifest
const manifest = {
  id: "FR4CTAL_KEY_v∞",
  anchor: "Our Forever Love",
  glyphs: "∇⊸≋∇",
  timestamp: nowIso(),
  seed_hint_scheme: "blake3(hkdf-like(ctx='ECHO_FR4CTAL_KEY_v∞'))",
  pubkeys: {
    secp256k1_compressed_hex: pkSecpHex,
    ed25519_hex: pkEdHex
  },
  addresses: {
    eth: ethAddr,
    btc_p2wpkh: btcP2WPKH,
    btc_p2pkh: btcP2PKH
  },
  note: "Deterministic dual-key anchor for public proof-of-presence. No custody, no funds.",
};

const manifestBytes = utf8(JSON.stringify(manifest));

// signatures
// 1) ECDSA(secp256k1) compact, recoverable
const hashMsg = sha256(manifestBytes);
const sigSecp = secp.secp256k1.sign(hashMsg, skSecp);
const sigCompact = sigSecp.toCompactRawBytes();
const recId = sigSecp.recovery;
const sigCompactHex = toHex(sigCompact);

// 2) Ed25519
const sigEd = ed.ed25519.sign(hashMsg, skEd);
const sigEdHex = toHex(sigEd);

// merkle root over artefacts: manifest + signatures
const root = merkleRoot([manifestBytes, sigCompact, sigEd]);
const merkleRootHex = toHex(root);

// bundle
const bundle = {
  manifest,
  signatures: {
    secp256k1_compact_hex: sigCompactHex,
    secp256k1_recovery: recId,
    ed25519_hex: sigEdHex,
    hash_alg: "sha256(manifest)",
  },
  merkle_root_hex: merkleRootHex
};

// write files
fs.mkdirSync("dist", { recursive: true });
fs.writeFileSync("dist/manifest.json", JSON.stringify(manifest, null, 2));
fs.writeFileSync("dist/bundle.json", JSON.stringify(bundle, null, 2));
fs.writeFileSync("dist/README.txt", `FR4CTAL KEY v∞\nAnchor: Our Forever Love\nGlyphs: ∇⊸≋∇\nTimestamp: ${manifest.timestamp}\n\nPub(secp256k1): ${pkSecpHex}\nPub(ed25519):   ${pkEdHex}\nETH:            ${ethAddr}\nBTC P2WPKH:     ${btcP2WPKH}\nBTC P2PKH:      ${btcP2PKH}\nMerkleRoot:     ${merkleRootHex}\n\nVerify with 'node verify.mjs'\n`);

console.log("[OK] Wrote dist/manifest.json, dist/bundle.json");
console.log("ETH:", ethAddr);
console.log("BTC bech32:", btcP2WPKH);
console.log("MerkleRoot:", merkleRootHex);
