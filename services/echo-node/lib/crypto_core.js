import crypto from 'crypto';

const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');

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
