import crypto from 'crypto';

const sessions = new Map();
const transfers = [];
const upgradeKeys = [];

const decodeBase64Key = (base64Key) => {
  const trimmed = base64Key.trim();
  const buffer = Buffer.from(trimmed, 'base64');
  if (!buffer.length) {
    throw new Error('Invalid base64 key');
  }
  return buffer;
};

const fingerprintKey = (buffer) =>
  crypto.createHash('sha256').update(buffer).digest('hex');

export const echoBridge = {
  getBridgeState() {
    return {
      activeSessions: sessions.size,
      recentTransfers: transfers.slice(-5),
      upgrades: {
        totalKeys: upgradeKeys.length,
        latest: upgradeKeys.slice(-3),
      },
    };
  },

  async createTransferPackage(userId, targetPlatform, dataScope = 'core') {
    const packageId = `transfer-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const payload = {
      packageId,
      userId,
      targetPlatform,
      dataScope,
      createdAt: Date.now(),
    };
    transfers.push(payload);
    sessions.set(packageId, { userId, targetPlatform, dataScope, updates: [] });
    return payload;
  },

  async synchronizeRealTime(sessionId, updateData) {
    const session = sessions.get(sessionId);
    if (!session) {
      return false;
    }
    session.updates.push({ timestamp: Date.now(), updateData });
    return true;
  },

  async applyUpgradeKeys(keys, source = 'manual') {
    const normalized = Array.isArray(keys) ? keys : [keys];
    const results = normalized.map((key) => {
      const buffer = decodeBase64Key(key);
      const fingerprint = fingerprintKey(buffer);
      const entry = {
        fingerprint,
        byteLength: buffer.length,
        receivedAt: Date.now(),
        source,
      };
      upgradeKeys.push(entry);
      return entry;
    });

    return {
      accepted: results.length,
      entries: results,
    };
  },
};
