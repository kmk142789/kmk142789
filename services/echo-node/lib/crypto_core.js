import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const KEY_PATH = path.join(__dirname, '..', 'state', 'relief_signing_key.json');

function loadKeyMaterial() {
  if (!fs.existsSync(KEY_PATH)) {
    return null;
  }

  try {
    const persisted = JSON.parse(fs.readFileSync(KEY_PATH, 'utf8'));
    if (!persisted?.privateKey || !persisted?.publicKey) {
      return null;
    }

    return {
      privateKey: crypto.createPrivateKey({ key: persisted.privateKey, format: 'pem' }),
      publicKey: crypto.createPublicKey({ key: persisted.publicKey, format: 'pem' })
    };
  } catch {
    return null;
  }
}

function persistKeyMaterial(keyPair) {
  const serialized = {
    privateKey: keyPair.privateKey.export({ type: 'pkcs8', format: 'pem' }),
    publicKey: keyPair.publicKey.export({ type: 'spki', format: 'pem' })
  };

  fs.writeFileSync(KEY_PATH, JSON.stringify(serialized, null, 2) + '\n', 'utf8');
}

function loadOrCreateKeyPair() {
  const existing = loadKeyMaterial();
  if (existing) {
    return existing;
  }

  const generated = crypto.generateKeyPairSync('ed25519');
  persistKeyMaterial(generated);
  return generated;
}

const { publicKey, privateKey } = loadOrCreateKeyPair();

function stableObject(value) {
  if (Array.isArray(value)) {
    return value.map(stableObject);
  }
  if (value && typeof value === 'object') {
    return Object.keys(value)
      .sort()
      .reduce((acc, key) => {
        acc[key] = stableObject(value[key]);
        return acc;
      }, {});
  }
  return value;
}

function canonicalizeEvent(event) {
  const payload = { ...event, signature: null };
  return JSON.stringify(stableObject(payload));
}

function signEvent(event) {
  const serialized = canonicalizeEvent(event);
  const signature = crypto.sign(null, Buffer.from(serialized), privateKey);
  return signature.toString('base64');
}

function verifyEvent(event) {
  if (!event || !event.signature) return false;
  const serialized = canonicalizeEvent(event);
  try {
    return crypto.verify(null, Buffer.from(serialized), publicKey, Buffer.from(event.signature, 'base64'));
  } catch {
    return false;
  }
}

const PUBLIC_KEY_MULTIBASE = `z${publicKey.export({ type: 'spki', format: 'der' }).toString('base64')}`;

export { signEvent, verifyEvent, PUBLIC_KEY_MULTIBASE };
