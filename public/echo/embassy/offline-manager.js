class OfflineManager {
  constructor({ localUrl, remoteUrl = null, cacheKey = 'echo-embassy-content-cache' }) {
    this.localUrl = localUrl;
    this.remoteUrl = remoteUrl;
    this.cacheKey = cacheKey;
    this.isOnline = navigator.onLine;
    this.content = null;
    this.lastSync = null;
    this.statusListeners = new Set();

    window.addEventListener('online', () => this.setOnlineState(true));
    window.addEventListener('offline', () => this.setOnlineState(false));
  }

  setOnlineState(isOnline) {
    this.isOnline = isOnline;
    this.notifyStatus();
  }

  onStatusChange(callback) {
    this.statusListeners.add(callback);
  }

  notifyStatus() {
    this.statusListeners.forEach((cb) => cb({ isOnline: this.isOnline, lastSync: this.lastSync }));
  }

  getCachedContent() {
    try {
      const raw = localStorage.getItem(this.cacheKey);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  setCachedContent(payload) {
    try {
      localStorage.setItem(this.cacheKey, JSON.stringify(payload));
      this.lastSync = new Date().toISOString();
    } catch {
      // Ignore caching failures; offline mode will still use in-memory content.
      this.lastSync = null;
    }
  }

  async fetchJson(url) {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Failed to load ${url} (${response.status})`);
    }
    return response.json();
  }

  async loadContent({ forceRemote = false } = {}) {
    // Priority: forced remote when online → automatic remote when online → cached → bundled local file.
    if ((forceRemote || this.isOnline) && this.remoteUrl) {
      try {
        const remote = await this.fetchJson(this.remoteUrl);
        this.content = remote;
        this.setCachedContent(remote);
        this.notifyStatus();
        return remote;
      } catch (err) {
        console.warn('[OfflineManager] Remote sync failed; falling back to cache/local', err);
      }
    }

    const cached = this.getCachedContent();
    if (cached) {
      this.content = cached;
      this.notifyStatus();
      return cached;
    }

    try {
      const local = await this.fetchJson(this.localUrl);
      this.content = local;
      this.setCachedContent(local);
      this.notifyStatus();
      return local;
    } catch (err) {
      console.error('[OfflineManager] Unable to load local content', err);
      this.content = null;
      this.notifyStatus();
      return null;
    }
  }

  async getContent(key, { forceRefresh = false } = {}) {
    if (!this.content || forceRefresh) {
      await this.loadContent({ forceRemote: forceRefresh });
    }
    return (this.content && this.content[key]) || null;
  }
}

window.OfflineManager = OfflineManager;
