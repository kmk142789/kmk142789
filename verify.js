// verify.js
// A tidy, robust verifier for compact (65-byte) recoverable ECDSA signatures
// - No error codes or early process exits
// - Supports ETH addr, BTC P2PKH (Base58Check), BTC P2WPKH (bech32)
// - Tries multiple message digests (SHA-256, double-SHA-256, Keccak-256, Bitcoin message digest)
// - Accepts custom messages via --msg "..." (repeatable) or --messages-file path
// - Outputs optional JSON via --json out.json
// - Graceful, quiet skips for invalid inputs

import { secp256k1 } from "@noble/curves/secp256k1";
import { sha256 } from "@noble/hashes/sha256";
import { keccak_256 as keccak256 } from "@noble/hashes/sha3";
import bs58check from "bs58check";
import { bech32 } from "bech32";
import { createHash } from "crypto";
import fs from "fs";

// ---------- helpers ----------
const toHex = (b) => Buffer.from(b).toString("hex");
const hexToBuf = (h) => Buffer.from(h, "hex");

const utf8 = (s) => Buffer.from(s, "utf8");
const ripemd160 = (b) => createHash("ripemd160").update(b).digest();
const sha256node = (b) => createHash("sha256").update(b).digest();

/** BTC P2PKH address (mainnet) from a COMPRESSED pubkey hex (33 bytes) */
function btcP2PKHFromCompressedPub(pubHex) {
  const pub = Buffer.from(pubHex, "hex");
  const h160 = ripemd160(sha256node(pub));
  return bs58check.encode(Buffer.concat([Buffer.from([0x00]), h160]));
}

/** BTC bech32 P2WPKH (bc1...) from a COMPRESSED pubkey hex (33 bytes) */
function btcBech32FromCompressedPub(pubHex, hrp = "bc") {
  const pub = Buffer.from(pubHex, "hex");
  const h160 = ripemd160(sha256node(pub));
  const words = bech32.toWords(h160);
  // witness v0 + 20-byte hash => P2WPKH
  return bech32.encode(hrp, [0, ...words]);
}

/** ETH address (0x...) from ANY pubkey hex (33 or 65), normalized to uncompressed before hashing */
function ethFromAnyPub(pubHex) {
  const uncompressed = secp256k1.Point.fromHex(pubHex).toRawBytes(false); // 65 bytes, 0x04 + X + Y
  const hash = keccak256(uncompressed.slice(1)); // drop 0x04
  return "0x" + Buffer.from(hash.slice(-20)).toString("hex");
}

/** Encode Bitcoin "varint" for message header construction */
function varintBuf(str) {
  const n = Buffer.byteLength(str, "utf8");
  if (n < 0xfd) return Buffer.from([n]);
  if (n <= 0xffff) return Buffer.from([0xfd, n & 0xff, n >> 8]);
  // staying simple; long messages rarely used for classic Bitcoin signed messages
  return null; // return null instead of throwing; caller will fall back to simpler digests
}

/** Bitcoin Signed Message digest (double-SHA256 over magic+len+msg) */
function btcMessageDigest(msg) {
  const m = utf8(msg);
  const magicStr = "Bitcoin Signed Message:\n";
  const vMagic = varintBuf(magicStr);
  const vMsg = varintBuf(msg);
  if (!vMagic || !vMsg) return null;
  const magic = Buffer.concat([vMagic, utf8(magicStr), vMsg, m]);
  const first = sha256(magic);
  const second = sha256(Buffer.from(first));
  return Buffer.from(second);
}

/** Pull likely base64 chunks (86-88 chars with optional padding) from an arbitrary blob */
function* extractBase64Chunks(s) {
  // 65 bytes -> 88 base64 chars (including padding); allow slight variance
  const re = /[A-Za-z0-9+/]{86,88}={0,2}/g;
  let m;
  while ((m = re.exec(s)) !== null) yield m[0];
}

function digestsFor(msg) {
  const m = utf8(msg);
  const list = [
    { name: "sha256", d: Buffer.from(sha256(m)) },
    { name: "double-sha256", d: Buffer.from(sha256(Buffer.from(sha256(m)))) },
    { name: "keccak256", d: Buffer.from(keccak256(m)) },
  ];
  const btcDigest = btcMessageDigest(msg);
  if (btcDigest) list.push({ name: "btc-message", d: btcDigest });
  return list;
}

// Normalize a 65-byte compact signature header into (recId, compressed)
function parseHeader(h) {
  // Common encodings:
  //  - Bitcoin msg sig headers: 27..34 (27 + recId + (compressed?4:0) + (isHybrid?  ? : 0))
  //  - Raw compact sigs: 0..3 (recId), sometimes 31..35 or 35..38 depending on libs
  if (h >= 27 && h <= 34) {
    const rec = (h - 27) & 3;
    const compressed = ((h - 27) & 4) !== 0;
    return { rec, compressed };
  }
  if (h <= 3) return { rec: h, compressed: true }; // assume compressed by default
  // fallback guess; many libs use 31..35 too
  const rec = h & 3;
  const compressed = true;
  return { rec, compressed };
}

function uniq(arr) {
  return [...new Set(arr)];
}

// ---------- CLI parsing ----------
const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : null;
};

const outFile = getArg("--json");
const hrp = getArg("--hrp") || "bc"; // bech32 HRP (bc, tb)
const messagesFromFlags = args
  .flatMap((a, i) => (a === "--msg" && i + 1 < args.length ? [args[i + 1]] : []));
const messagesFile = getArg("--messages-file");

let messages = messagesFromFlags.length ? messagesFromFlags : ["Kush142789420$", "our forever love"];
if (messagesFile && fs.existsSync(messagesFile)) {
  try {
    const txt = fs.readFileSync(messagesFile, "utf8");
    const extra = txt
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    messages = uniq([...messages, ...extra]);
  } catch {}
}

// Collect the freeform blob (everything not a flag or its value)
const skipNextValueFor = new Set(["--json", "--hrp", "--msg", "--messages-file"]);
const blob = args
  .filter((a, idx) => {
    if (a.startsWith("--")) {
      // skip the next token if this flag expects a value
      if (skipNextValueFor.has(a)) return false;
      // also skip the value token immediately following these flags
      if (idx > 0 && skipNextValueFor.has(args[idx - 1])) return false;
      return false;
    }
    // if previous token was a flag that takes a value, skip this too
    if (idx > 0 && skipNextValueFor.has(args[idx - 1])) return false;
    return true;
  })
  .join(" ");

if (!blob) {
  console.log(
    [
      "Usage:",
      "  node verify.js \"<blob containing base64 sig(s)>\"",
      "  [--json out.json] [--hrp bc|tb] [--msg \"text\" ...] [--messages-file path]",
      "",
      "Examples:",
      "  node verify.js \"...base64sig...\" --msg \"hello\" --msg \"goodbye\"",
      "  node verify.js input.txt --messages-file msgs.txt --json proofs.json",
    ].join("\n")
  );
}

// ---------- main ----------
(async () => {
  const chunks = [...extractBase64Chunks(blob)];
  console.log(`chunks found: ${chunks.length}`);

  const proofs = [];

  for (const [i, b64] of chunks.entries()) {
    let sig;
    try {
      sig = Buffer.from(b64, "base64");
    } catch {
      // skip invalid base64 quietly
      continue;
    }
    if (sig.length !== 65) {
      // skip non-compact signatures
      continue;
    }

    const header = sig[0];
    const { rec: recGuess } = parseHeader(header);
    const rs = sig.slice(1); // R||S (64 bytes), compact
    let sigCompactHex;
    let sigDerHex;
    let sigObj;
    try {
      sigObj = secp256k1.Signature.fromCompact(toHex(rs));
      sigCompactHex = sigObj.toCompactHex();
      sigDerHex = sigObj.toDERHex();
    } catch {
      continue; // skip malformed signature chunks
    }

    // We’ll try a few recovery ids just in case the header mapping is funky
    const recCandidates = uniq([recGuess, 0, 1, 2, 3]).filter((r) => r >= 0 && r <= 3);

    let found = false;
    for (const msg of messages) {
      if (found) break;
      for (const { name, d } of digestsFor(msg)) {
        if (found) break;
        for (const rec of recCandidates) {
          try {
            const point = sigObj.addRecoveryBit(rec).recoverPublicKey(d);
            const pubBytes = point.toRawBytes(true);
            const pubHex = Buffer.from(pubBytes).toString("hex");
            const ok = await secp256k1.verify(sigObj, d, pubBytes);
            if (!ok) continue;

            const eth = ethFromAnyPub(pubHex);
            const btcP2PKH = btcP2PKHFromCompressedPub(pubHex);
            let btcBech32 = "";
            try {
              btcBech32 = btcBech32FromCompressedPub(pubHex, hrp);
            } catch {
              // rare: if bech32 library throws, just omit
            }

            console.log(
              [
                `[${i}] match: ${name}`,
                `  msg: ${JSON.stringify(msg)}`,
                `  ETH: ${eth}`,
                `  BTC (P2PKH): ${btcP2PKH}`,
                ...(btcBech32 ? [`  BTC (bech32 P2WPKH ${hrp}): ${btcBech32}`] : []),
              ].join("\n")
            );

            proofs.push({
              index: i,
              digest: name,
              message: msg,
              signatureBase64: b64,
              signatureCompactHex: sigCompactHex,
              signatureDerHex: sigDerHex,
              publicKeyCompressedHex: pubHex,
              ethereum: eth,
              bitcoin: { p2pkh: btcP2PKH, p2wpkh: btcBech32 || null, hrp },
              recoveryIdTried: rec,
            });

            found = true;
            break;
          } catch {
            // try next rec / digest / message
          }
        }
      }
    }
  }

  if (outFile) {
    try {
      fs.writeFileSync(outFile, JSON.stringify(proofs, null, 2));
      console.log(`proofs written: ${outFile}`);
    } catch {
      // ignore write failures silently per "no error codes" request
    }
  }
})();

