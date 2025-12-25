const STORAGE_KEY = 'echo-embassy-state-v1';
const OFFLINE_INDICATOR = document.getElementById('offline-indicator');
const PERSISTENCE_INDICATOR = document.getElementById('persistence-indicator');
const SIGNAL_INDICATOR = document.getElementById('signal-indicator');
const portraitDetails = document.getElementById('portrait-details');
const portraitSignal = document.getElementById('portrait-signal');
const channelStatus = document.getElementById('channel-status');
const waypointStatus = document.getElementById('waypoint-status');
const integrationStatus = document.getElementById('integration-status');
const dispatchStatus = document.getElementById('dispatch-status');
const resonanceBar = document.getElementById('resonance-bar');
const pulseLog = document.getElementById('pulse-log');

const scene = document.querySelector('a-scene');
const rig = document.getElementById('rig');
const hall = document.getElementById('hall');
const hallLights = document.getElementById('hall-lights');
const echoButterflies = document.getElementById('echo-butterflies');
const echoSilhouette = document.getElementById('echo-silhouette');
const echoCompanion = document.getElementById('echo-companion');
const forgeSandbox = document.getElementById('forge-sandbox');
const sandSculptures = document.getElementById('sand-sculptures');
const trees = document.querySelectorAll('.tree');
const beaconHall = document.getElementById('beacon-hall');
const beaconGardens = document.getElementById('beacon-gardens');
const beaconPlaza = document.getElementById('beacon-plaza');

const forgeCreate = document.getElementById('forge-create');
const forgeClear = document.getElementById('forge-clear');
const gardenGrow = document.getElementById('garden-grow');
const gardenSculpt = document.getElementById('garden-sculpt');
const gardenScore = document.getElementById('garden-score');
const soundAdd = document.getElementById('sound-add');
const soundToggle = document.getElementById('sound-toggle');
const channelOpen = document.getElementById('channel-open');
const channelBrief = document.getElementById('channel-brief');
const channelSeal = document.getElementById('channel-seal');
const integrationOpen = document.getElementById('integration-open');
const integrationLog = document.getElementById('integration-log');
const pulseSync = document.getElementById('pulse-sync');
const pulseReset = document.getElementById('pulse-reset');

const echoButtons = document.querySelectorAll('[data-echo-form]');
const hallButtons = document.querySelectorAll('[data-hall-mode]');
const waypointButtons = document.querySelectorAll('[data-waypoint]');

const AI_STUDIO_URL = 'https://ai.studio/apps/drive/1qV1fdsj4zHePTCiZt8G1VMTxD-3SdYAW';
const FORGE_RELIC_LIMIT = 12;
const SCULPTURE_LIMIT = 10;
const SOUND_LOOP_LIMIT = 6;
const PORTRAIT_COOLDOWN_MS = 1200;

const hallModes = {
  council: {
    scale: '1 1 1',
    light: { color: '#8ec5ff', intensity: 1.2 },
    ambient: { color: '#1e3a8a', intensity: 0.5 }
  },
  whisper: {
    scale: '0.8 0.85 0.8',
    light: { color: '#c4b5fd', intensity: 0.7 },
    ambient: { color: '#312e81', intensity: 0.35 }
  },
  celebrate: {
    scale: '1.2 1.1 1.3',
    light: { color: '#fbbf24', intensity: 1.6 },
    ambient: { color: '#1e293b', intensity: 0.6 }
  }
};

const relicPalettes = [
  { color: '#38bdf8', emissive: '#0ea5e9' },
  { color: '#f472b6', emissive: '#f9a8d4' },
  { color: '#a855f7', emissive: '#c084fc' },
  { color: '#facc15', emissive: '#f97316' }
];

const defaultState = {
  echoForm: 'companion',
  hallMode: 'council',
  trees: [1, 1.1, 1.2],
  forgeRelics: [],
  sculptures: [],
  soundLoops: [],
  ambienceOn: false,
  waypoint: 'hall',
  activeChannel: 'standby',
  integrationNode: 'Unlinked',
  resonance: 0.72,
  lastDispatch: 'Awaiting briefing',
  pulseLog: []
};

let audioContext = null;
let ambienceNodes = [];
let state = loadState();
let activePortrait = null;
let lastPortraitAt = 0;
const portraitState = new Map();
let portraitProfiles = {};
let avatarKnowledge = {
  rooms: {},
  orgs: []
};
let offlineManager = null;
let registryById = new Map();
let avatarState = 'idle';
let avatarStateTimer = null;

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { ...defaultState };
    }
    const parsed = JSON.parse(raw);
    return { ...defaultState, ...parsed };
  } catch {
    return { ...defaultState };
  }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    PERSISTENCE_INDICATOR.textContent = 'Persistence synced';
  } catch {
    PERSISTENCE_INDICATOR.textContent = 'Persistence limited';
  }
}

function updateMissionConsole() {
  channelStatus.textContent = formatChannel(state.activeChannel);
  waypointStatus.textContent = formatWaypoint(state.waypoint);
  integrationStatus.textContent = state.integrationNode;
  dispatchStatus.textContent = state.lastDispatch;
  resonanceBar.style.width = `${Math.round(state.resonance * 100)}%`;
  SIGNAL_INDICATOR.textContent = `Signal ${formatChannel(state.activeChannel)}`;
  renderPulseLog();
}

function formatChannel(channel) {
  switch (channel) {
    case 'open':
      return 'Open channel';
    case 'brief':
      return 'Briefing dispatched';
    case 'sealed':
      return 'Dispatch sealed';
    default:
      return 'Standby';
  }
}

function formatWaypoint(waypoint) {
  switch (waypoint) {
    case 'gardens':
      return 'Celestial Gardens';
    case 'plaza':
      return 'Gravity Plaza';
    default:
      return 'Hall of Parity';
  }
}

function renderPulseLog() {
  pulseLog.innerHTML = '';
  state.pulseLog.forEach((entry) => {
    const item = document.createElement('li');
    item.textContent = entry;
    pulseLog.appendChild(item);
  });
}

function addPulseLog(message) {
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  state.pulseLog.unshift(`${timestamp} · ${message}`);
  state.pulseLog = state.pulseLog.slice(0, 6);
  saveState();
  renderPulseLog();
}

function setEchoForm(form) {
  state.echoForm = form;
  echoButterflies.setAttribute('visible', form === 'butterflies');
  echoSilhouette.setAttribute('visible', form === 'silhouette');
  echoCompanion.setAttribute('visible', form === 'companion');
  saveState();
}

function setHallMode(mode) {
  const config = hallModes[mode];
  if (!config) return;
  state.hallMode = mode;
  hall.setAttribute('scale', config.scale);

  const light = hallLights.querySelector('a-light[type="point"]');
  const ambient = hallLights.querySelector('a-light[type="ambient"]');
  light.setAttribute('color', config.light.color);
  light.setAttribute('intensity', config.light.intensity);
  ambient.setAttribute('color', config.ambient.color);
  ambient.setAttribute('intensity', config.ambient.intensity);
  addPulseLog(`Hall shifted to ${mode} mode.`);
  saveState();
}

function updateTrees() {
  trees.forEach((tree, index) => {
    const height = state.trees[index] || 1.1;
    tree.setAttribute('height', height * 2);
    tree.setAttribute('position', `${tree.getAttribute('position').x} ${height} ${tree.getAttribute('position').z}`);
  });
  saveState();
}

function growTrees() {
  state.trees = state.trees.map((value) => Math.min(value + 0.15, 2));
  updateTrees();
}

function ensureRelicDefaults(relic) {
  const palette = relicPalettes.find((item) => item.color === relic.color) || relicPalettes[0];
  return {
    ...relic,
    emissive: relic.emissive || palette.emissive,
    spin: relic.spin ?? (4000 + Math.floor(Math.random() * 4000)),
    pulse: relic.pulse ?? (0.9 + Math.random() * 0.3)
  };
}

function ensureSculptureDefaults(sculpture) {
  return {
    ...sculpture,
    tone: sculpture.tone || '#facc15',
    shimmer: sculpture.shimmer ?? (2200 + Math.floor(Math.random() * 2000))
  };
}

function removeEntityById(id) {
  const entity = document.getElementById(id);
  if (entity && entity.parentElement) {
    entity.parentElement.removeChild(entity);
  }
}

function trimForgeRelics() {
  while (state.forgeRelics.length > FORGE_RELIC_LIMIT) {
    const removed = state.forgeRelics.shift();
    if (removed?.id) {
      removeEntityById(removed.id);
    }
  }
}

function trimSculptures() {
  while (state.sculptures.length > SCULPTURE_LIMIT) {
    const removed = state.sculptures.shift();
    if (removed?.id) {
      removeEntityById(removed.id);
    }
  }
}

function applyRelicStyle(entity, relic) {
  entity.setAttribute('material', {
    color: relic.color,
    emissive: relic.emissive,
    emissiveIntensity: 0.55,
    metalness: 0.8,
    roughness: 0.2
  });
  entity.setAttribute('animation__spin', `property: rotation; to: 0 360 0; loop: true; dur: ${relic.spin}; easing: linear`);
  entity.setAttribute('animation__pulse', `property: scale; dir: alternate; dur: 1200; loop: true; to: ${relic.pulse} ${relic.pulse} ${relic.pulse}`);
}

function applySculptureStyle(entity, sculpture) {
  entity.setAttribute('material', {
    color: sculpture.tone,
    emissive: '#fef3c7',
    emissiveIntensity: 0.35,
    metalness: 0.2,
    roughness: 0.4
  });
  entity.setAttribute('animation__shimmer', `property: rotation; to: 0 360 0; loop: true; dur: ${sculpture.shimmer}; easing: linear`);
}

function bindRelicInteractions(entity, relic) {
  entity.addEventListener('click', () => {
    addPulseLog(`Relic ${relic.id} attuned at ${Math.round(relic.pulse * 100)}% resonance.`);
  });
}

function createForgeRelic() {
  const id = `relic-${Date.now()}`;
  const type = Math.random() > 0.5 ? 'a-box' : 'a-sphere';
  const x = (Math.random() - 0.5) * 2;
  const y = 1 + Math.random();
  const z = (Math.random() - 0.5) * 2;
  const palette = relicPalettes[Math.floor(Math.random() * relicPalettes.length)];
  const color = palette.color;
  const emissive = palette.emissive;

  const entity = document.createElement(type);
  entity.setAttribute('id', id);
  entity.setAttribute('position', `${x} ${y} ${z}`);
  entity.setAttribute('depth', 0.4);
  entity.setAttribute('height', 0.4);
  entity.setAttribute('width', 0.4);
  entity.setAttribute('radius', 0.25);
  entity.setAttribute('class', 'forge-relic');

  const relic = ensureRelicDefaults({ id, type, position: { x, y, z }, color, emissive });
  applyRelicStyle(entity, relic);
  bindRelicInteractions(entity, relic);

  forgeSandbox.appendChild(entity);
  state.forgeRelics.push(relic);
  trimForgeRelics();
  addPulseLog('Relic forged in the Haptic Forge.');
  saveState();
}

function restoreForgeRelics() {
  forgeSandbox.innerHTML = '';
  state.forgeRelics = state.forgeRelics.map(ensureRelicDefaults);
  state.forgeRelics.forEach((relic) => {
    const entity = document.createElement(relic.type);
    entity.setAttribute('id', relic.id);
    entity.setAttribute('position', `${relic.position.x} ${relic.position.y} ${relic.position.z}`);
    entity.setAttribute('depth', 0.4);
    entity.setAttribute('height', 0.4);
    entity.setAttribute('width', 0.4);
    entity.setAttribute('radius', 0.25);
    entity.setAttribute('class', 'forge-relic');
    applyRelicStyle(entity, relic);
    bindRelicInteractions(entity, relic);
    forgeSandbox.appendChild(entity);
  });
  trimForgeRelics();
}

function clearForge() {
  state.forgeRelics = [];
  forgeSandbox.innerHTML = '';
  addPulseLog('Forge cleared for new relics.');
  saveState();
}

function createSculpture() {
  const id = `sculpt-${Date.now()}`;
  const height = 0.6 + Math.random() * 1.2;
  const x = (Math.random() - 0.5) * 4;
  const z = (Math.random() - 0.5) * 4;
  const tone = Math.random() > 0.5 ? '#facc15' : '#fde68a';
  const entity = document.createElement('a-cylinder');
  entity.setAttribute('id', id);
  entity.setAttribute('position', `${x} ${height / 2} ${z}`);
  entity.setAttribute('radius', 0.35);
  entity.setAttribute('height', height);
  const sculpture = ensureSculptureDefaults({ id, height, x, z, tone });
  applySculptureStyle(entity, sculpture);
  sandSculptures.appendChild(entity);
  state.sculptures.push(sculpture);
  trimSculptures();
  addPulseLog('Light-sand sculpture sculpted.');
  saveState();
}

function restoreSculptures() {
  sandSculptures.innerHTML = '';
  state.sculptures = state.sculptures.map(ensureSculptureDefaults);
  state.sculptures.forEach((sculpt) => {
    const entity = document.createElement('a-cylinder');
    entity.setAttribute('id', sculpt.id);
    entity.setAttribute('position', `${sculpt.x} ${sculpt.height / 2} ${sculpt.z}`);
    entity.setAttribute('radius', 0.35);
    entity.setAttribute('height', sculpt.height);
    applySculptureStyle(entity, sculpt);
    sandSculptures.appendChild(entity);
  });
  trimSculptures();
}

function judgeSculptures() {
  const score = Math.min(100, Math.round(state.sculptures.length * 12 + Math.random() * 20));
  portraitDetails.textContent = `The portraits award ${score} Echo Fragments for the latest light-sand creations.`;
  portraitSignal.textContent = 'Portrait council convened.';
  addPulseLog(`Portrait council scored the sands: ${score} fragments.`);
}

function ensureAudio() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
}

function addSoundLoop() {
  ensureAudio();
  if (ambienceNodes.length >= SOUND_LOOP_LIMIT) {
    const oldNode = ambienceNodes.shift();
    if (oldNode) {
      oldNode.oscillator.stop();
      oldNode.oscillator.disconnect();
      oldNode.gain.disconnect();
    }
    state.soundLoops.shift();
  }
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  oscillator.type = 'sine';
  oscillator.frequency.value = 160 + Math.random() * 240;
  gain.gain.value = 0.03;
  oscillator.connect(gain).connect(audioContext.destination);
  oscillator.start();
  ambienceNodes.push({ oscillator, gain });
  state.soundLoops.push({ frequency: oscillator.frequency.value });
  addPulseLog('Zen stream melody captured.');
  saveState();
}

function toggleAmbience() {
  ensureAudio();
  state.ambienceOn = !state.ambienceOn;
  ambienceNodes.forEach(({ gain }) => {
    gain.gain.value = state.ambienceOn ? 0.03 : 0.0;
  });
  addPulseLog(state.ambienceOn ? 'Ambience awakened.' : 'Ambience muted.');
  saveState();
}

function restoreSoundLoops() {
  if (!state.soundLoops.length) {
    return;
  }
  ensureAudio();
  state.soundLoops = state.soundLoops.slice(-SOUND_LOOP_LIMIT);
  state.soundLoops.forEach((loop) => {
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = loop.frequency;
    gain.gain.value = state.ambienceOn ? 0.03 : 0.0;
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
    ambienceNodes.push({ oscillator, gain });
  });
}

function initializePortraits() {
  document.querySelectorAll('.portrait').forEach((portrait) => {
    const material = portrait.getAttribute('material') || {};
    portraitState.set(portrait, {
      baseColor: material.color,
      emissive: material.emissive,
      emissiveIntensity: material.emissiveIntensity
    });
  });
}

function activatePortrait(target, portrait, { log = true } = {}) {
  const profile = portraitProfiles[portrait];
  if (!profile) {
    return;
  }
  const now = Date.now();
  if (portrait === activePortrait && now - lastPortraitAt < PORTRAIT_COOLDOWN_MS) {
    return;
  }
  activePortrait = portrait;
  lastPortraitAt = now;
  const line = profile.lines[Math.floor(Math.random() * profile.lines.length)];
  portraitDetails.textContent = line;
  if (portraitSignal) {
    portraitSignal.textContent = profile.signal;
  }
  target.setAttribute('material', 'emissive', profile.glow);
  target.setAttribute('material', 'emissiveIntensity', 0.8);
  target.setAttribute('animation__pulse', 'property: scale; dir: alternate; dur: 500; loop: true; to: 1.04 1.04 1.04');
  if (log) {
    addPulseLog(`${portrait} shared a new reflection.`);
  }
}

function resetPortrait() {
  portraitDetails.textContent = 'Approach or tap a portrait in VR to hear its voice.';
  if (portraitSignal) {
    portraitSignal.textContent = 'Listening for portrait voices.';
  }
  document.querySelectorAll('.portrait').forEach((portrait) => {
    const base = portraitState.get(portrait);
    if (base) {
      if (base.emissive) {
        portrait.setAttribute('material', 'emissive', base.emissive);
        portrait.setAttribute('material', 'emissiveIntensity', base.emissiveIntensity || 0);
      } else {
        portrait.setAttribute('material', 'emissive', '#000000');
        portrait.setAttribute('material', 'emissiveIntensity', 0);
      }
    }
    portrait.removeAttribute('animation__pulse');
    portrait.setAttribute('scale', '1 1 1');
  });
  activePortrait = null;
}

function handlePortraitHover(event) {
  const target = event.target;
  const portrait = target.getAttribute('data-portrait');
  if (!portrait) return;
  activatePortrait(target, portrait, { log: false });
}

function handlePortraitClick(event) {
  const target = event.target;
  const portrait = target.getAttribute('data-portrait');
  if (!portrait) return;
  activatePortrait(target, portrait, { log: true });
}

function updateOnlineStatus() {
  OFFLINE_INDICATOR.textContent = navigator.onLine ? 'Online' : 'Offline-ready';
}

function applyWaypoint(waypoint, { log = true } = {}) {
  const positions = {
    hall: '0 1.6 8',
    gardens: '0 1.6 -12',
    plaza: '6 1.6 -16'
  };
  const target = positions[waypoint] || positions.hall;
  rig.setAttribute('position', target);
  state.waypoint = waypoint;
  updateBeaconState(waypoint);
  if (log) {
    addPulseLog(`Wayfinding engaged: ${formatWaypoint(waypoint)}.`);
    saveState();
    updateMissionConsole();
  }
}

function setWaypoint(waypoint) {
  applyWaypoint(waypoint, { log: true });
}

function updateBeaconState(active) {
  beaconHall.setAttribute('color', active === 'hall' ? '#38bdf8' : '#64748b');
  beaconGardens.setAttribute('color', active === 'gardens' ? '#38bdf8' : '#64748b');
  beaconPlaza.setAttribute('color', active === 'plaza' ? '#38bdf8' : '#64748b');
}

function updateChannelStatus(status, message) {
  state.activeChannel = status;
  state.lastDispatch = message;
  SIGNAL_INDICATOR.textContent = `Signal ${formatChannel(status)}`;
  addPulseLog(message);
  saveState();
  updateMissionConsole();
}

function setIntegrationNode(message) {
  state.integrationNode = message;
  updateMissionConsole();
  saveState();
}

function openIntegrationPortal() {
  window.open(AI_STUDIO_URL, '_blank', 'noopener,noreferrer');
  setIntegrationNode('AI Studio Drive linked');
  addPulseLog('Integration portal opened for shared dossiers.');
}

function logIntegration() {
  setIntegrationNode('AI Studio Drive handshake logged');
  updateChannelStatus('brief', 'Integration brief logged for AI Studio Drive.');
}

function syncPulse() {
  state.resonance = Math.min(1, state.resonance + 0.08);
  addPulseLog('Resonance pulse synchronized.');
  saveState();
  updateMissionConsole();
}

function resetPulse() {
  state.resonance = 0.4;
  addPulseLog('Resonance recalibrated to baseline.');
  saveState();
  updateMissionConsole();
}

function driftResonance() {
  const drift = (Math.random() - 0.5) * 0.04;
  state.resonance = Math.min(1, Math.max(0.2, state.resonance + drift));
  updateMissionConsole();
  saveState();
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register('sw.js')
      .catch(() => {
        OFFLINE_INDICATOR.textContent = 'Offline cache unavailable';
      });
  }
}

async function bootstrapContent() {
  offlineManager = new OfflineManager({
    localUrl: 'embassy-content.json',
    remoteUrl: 'https://raw.githubusercontent.com/kmk142789/main/public/echo/embassy/embassy-content.json',
    cacheKey: 'echo-embassy-content-cache'
  });

  offlineManager.onStatusChange(({ isOnline, lastSync }) => {
    OFFLINE_INDICATOR.textContent = isOnline ? 'Online' : 'Offline-ready';
    if (lastSync) {
      PERSISTENCE_INDICATOR.textContent = `Cached · ${new Date(lastSync).toLocaleTimeString()}`;
    }
  });

  const content = (await offlineManager.loadContent()) || {};
  portraitProfiles = mapPortraitsByTitle(content.portraits || []);
  avatarKnowledge.rooms = content.echoAvatar?.rooms || {};
  avatarKnowledge.orgs = content.echoAvatar?.orgs || [];
  registryById = new Map((avatarKnowledge.orgs || []).map((org) => [org.id, org]));
  initializePortraits();
  initializeAvatarStates();
}

function mapPortraitsByTitle(portraits) {
  const entries = {};
  portraits.forEach((portrait) => {
    const title = portrait.title || portrait.id;
    entries[title] = {
      signal: `${portrait.type || 'Lore'} signal steady`,
      glow: pickGlowForType(portrait.type),
      lines: portrait.lines || []
    };
  });
  // Preserve legacy names if missing from content.
  if (!entries.Chronicler) {
    entries.Chronicler = {
      signal: 'Archive clarity online',
      glow: '#38bdf8',
      lines: ['I have indexed today’s arrivals and the path you walked through the hall.']
    };
  }
  return entries;
}

function pickGlowForType(type) {
  switch ((type || '').toLowerCase()) {
    case 'history':
      return '#38bdf8';
    case 'humor':
      return '#fb923c';
    case 'system':
      return '#f8fafc';
    case 'lore':
    default:
      return '#a855f7';
  }
}

function initializeAvatarStates() {
  clearTimeout(avatarStateTimer);
  avatarState = 'idle';
  avatarStateTimer = setTimeout(() => setAvatarState('greet'), 1200);
}

function setAvatarState(nextState) {
  avatarState = nextState;
  switch (nextState) {
    case 'greet':
      addPulseLog('Echo avatar: Welcome envoy—select a hall or follow the beacons.');
      scheduleAvatarState('tour', 4200);
      break;
    case 'tour':
      describeCurrentWaypoint();
      scheduleAvatarState('idle', 5200);
      break;
    case 'qna':
      addPulseLog('Echo avatar: Ask anything; offline knowledge is ready.');
      scheduleAvatarState('idle', 6200);
      break;
    case 'idle':
    default:
      scheduleAvatarState('ambient', 8000);
      break;
    case 'ambient':
      addPulseLog('Echo avatar hums softly, syncing with resonance.');
      scheduleAvatarState('idle', 12000);
      break;
  }
}

function scheduleAvatarState(target, delay) {
  clearTimeout(avatarStateTimer);
  avatarStateTimer = setTimeout(() => setAvatarState(target), delay);
}

function describeCurrentWaypoint() {
  const roomKey = state.waypoint || 'hall';
  const description = avatarKnowledge.rooms[roomKey];
  if (description) {
    addPulseLog(`Echo avatar describes ${formatWaypoint(roomKey)}: ${description}`);
  } else {
    addPulseLog(`Echo avatar notes ${formatWaypoint(roomKey)} awaits your footsteps.`);
  }
}

function getOrgById(id) {
  return registryById.get(id) || null;
}

function listOrgsByType(type) {
  return (avatarKnowledge.orgs || []).filter((org) => org.type === type);
}

scene.addEventListener('loaded', () => {
  bootstrapContent().finally(() => {
    setEchoForm(state.echoForm);
    setHallMode(state.hallMode);
    updateTrees();
    restoreForgeRelics();
    restoreSculptures();
    restoreSoundLoops();
    applyWaypoint(state.waypoint, { log: false });
    updateMissionConsole();
  });
});

forgeCreate.addEventListener('click', createForgeRelic);
forgeClear.addEventListener('click', clearForge);

soundAdd.addEventListener('click', addSoundLoop);
soundToggle.addEventListener('click', toggleAmbience);
channelOpen.addEventListener('click', () => updateChannelStatus('open', 'Diplomatic channel opened to partner envoys.'));
channelBrief.addEventListener('click', () => updateChannelStatus('brief', 'Briefing dispatched to allied nodes.'));
channelSeal.addEventListener('click', () => updateChannelStatus('sealed', 'Dispatch sealed and archived.'));
integrationOpen.addEventListener('click', openIntegrationPortal);
integrationLog.addEventListener('click', logIntegration);
pulseSync.addEventListener('click', syncPulse);
pulseReset.addEventListener('click', resetPulse);

if (gardenGrow) {
  gardenGrow.addEventListener('click', growTrees);
}

if (gardenSculpt) {
  gardenSculpt.addEventListener('click', createSculpture);
}

if (gardenScore) {
  gardenScore.addEventListener('click', judgeSculptures);
}

echoButtons.forEach((button) => {
  button.addEventListener('click', () => setEchoForm(button.dataset.echoForm));
});

hallButtons.forEach((button) => {
  button.addEventListener('click', () => setHallMode(button.dataset.hallMode));
});

waypointButtons.forEach((button) => {
  button.addEventListener('click', () => setWaypoint(button.dataset.waypoint));
});

document.querySelectorAll('.portrait').forEach((portrait) => {
  portrait.addEventListener('mouseenter', handlePortraitHover);
  portrait.addEventListener('mouseleave', resetPortrait);
  portrait.addEventListener('click', handlePortraitClick);
});

updateOnlineStatus();
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
setInterval(driftResonance, 7000);
registerServiceWorker();
