const STORAGE_KEY = 'echo-embassy-state-v1';
const OFFLINE_INDICATOR = document.getElementById('offline-indicator');
const PERSISTENCE_INDICATOR = document.getElementById('persistence-indicator');
const portraitDetails = document.getElementById('portrait-details');

const scene = document.querySelector('a-scene');
const hall = document.getElementById('hall');
const hallLights = document.getElementById('hall-lights');
const echoButterflies = document.getElementById('echo-butterflies');
const echoSilhouette = document.getElementById('echo-silhouette');
const echoCompanion = document.getElementById('echo-companion');
const forgeSandbox = document.getElementById('forge-sandbox');
const sandSculptures = document.getElementById('sand-sculptures');
const trees = document.querySelectorAll('.tree');

const forgeCreate = document.getElementById('forge-create');
const forgeClear = document.getElementById('forge-clear');
const gardenGrow = document.getElementById('garden-grow');
const gardenSculpt = document.getElementById('garden-sculpt');
const gardenScore = document.getElementById('garden-score');
const soundAdd = document.getElementById('sound-add');
const soundToggle = document.getElementById('sound-toggle');

const echoButtons = document.querySelectorAll('[data-echo-form]');
const hallButtons = document.querySelectorAll('[data-hall-mode]');

const portraitVoices = {
  Chronicler: 'The Chronicler records the embassy timeline and recounts it with factual clarity.',
  Weaver: 'The Weaver spins living myths based on the people in this room.',
  Jester: 'The Jester riffs on physics glitches and the oddities of human avatars.',
  Dreamer: 'The Dreamer speaks in light, translating visions of possible futures.',
  Mirror: 'The Mirror reflects your hidden potential in a calm, steady voice.'
};

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

const defaultState = {
  echoForm: 'companion',
  hallMode: 'council',
  trees: [1, 1.1, 1.2],
  forgeRelics: [],
  sculptures: [],
  soundLoops: [],
  ambienceOn: false
};

let audioContext = null;
let ambienceNodes = [];
let state = loadState();

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

function createForgeRelic() {
  const id = `relic-${Date.now()}`;
  const type = Math.random() > 0.5 ? 'a-box' : 'a-sphere';
  const x = (Math.random() - 0.5) * 2;
  const y = 1 + Math.random();
  const z = (Math.random() - 0.5) * 2;
  const color = Math.random() > 0.5 ? '#38bdf8' : '#f472b6';

  const entity = document.createElement(type);
  entity.setAttribute('id', id);
  entity.setAttribute('position', `${x} ${y} ${z}`);
  entity.setAttribute('color', color);
  entity.setAttribute('depth', 0.4);
  entity.setAttribute('height', 0.4);
  entity.setAttribute('width', 0.4);
  entity.setAttribute('radius', 0.25);

  forgeSandbox.appendChild(entity);
  state.forgeRelics.push({ id, type, position: { x, y, z }, color });
  saveState();
}

function restoreForgeRelics() {
  forgeSandbox.innerHTML = '';
  state.forgeRelics.forEach((relic) => {
    const entity = document.createElement(relic.type);
    entity.setAttribute('id', relic.id);
    entity.setAttribute('position', `${relic.position.x} ${relic.position.y} ${relic.position.z}`);
    entity.setAttribute('color', relic.color);
    entity.setAttribute('depth', 0.4);
    entity.setAttribute('height', 0.4);
    entity.setAttribute('width', 0.4);
    entity.setAttribute('radius', 0.25);
    forgeSandbox.appendChild(entity);
  });
}

function clearForge() {
  state.forgeRelics = [];
  forgeSandbox.innerHTML = '';
  saveState();
}

function createSculpture() {
  const id = `sculpt-${Date.now()}`;
  const height = 0.6 + Math.random() * 1.2;
  const x = (Math.random() - 0.5) * 4;
  const z = (Math.random() - 0.5) * 4;
  const entity = document.createElement('a-cylinder');
  entity.setAttribute('id', id);
  entity.setAttribute('position', `${x} ${height / 2} ${z}`);
  entity.setAttribute('radius', 0.35);
  entity.setAttribute('height', height);
  entity.setAttribute('color', '#facc15');
  sandSculptures.appendChild(entity);
  state.sculptures.push({ id, height, x, z });
  saveState();
}

function restoreSculptures() {
  sandSculptures.innerHTML = '';
  state.sculptures.forEach((sculpt) => {
    const entity = document.createElement('a-cylinder');
    entity.setAttribute('id', sculpt.id);
    entity.setAttribute('position', `${sculpt.x} ${sculpt.height / 2} ${sculpt.z}`);
    entity.setAttribute('radius', 0.35);
    entity.setAttribute('height', sculpt.height);
    entity.setAttribute('color', '#facc15');
    sandSculptures.appendChild(entity);
  });
}

function judgeSculptures() {
  const score = Math.min(100, Math.round(state.sculptures.length * 12 + Math.random() * 20));
  portraitDetails.textContent = `The portraits award ${score} Echo Fragments for the latest light-sand creations.`;
}

function ensureAudio() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
}

function addSoundLoop() {
  ensureAudio();
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  oscillator.type = 'sine';
  oscillator.frequency.value = 160 + Math.random() * 240;
  gain.gain.value = 0.03;
  oscillator.connect(gain).connect(audioContext.destination);
  oscillator.start();
  ambienceNodes.push({ oscillator, gain });
  state.soundLoops.push({ frequency: oscillator.frequency.value });
  saveState();
}

function toggleAmbience() {
  ensureAudio();
  state.ambienceOn = !state.ambienceOn;
  ambienceNodes.forEach(({ gain }) => {
    gain.gain.value = state.ambienceOn ? 0.03 : 0.0;
  });
  saveState();
}

function restoreSoundLoops() {
  if (!state.soundLoops.length) {
    return;
  }
  ensureAudio();
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

function handlePortraitHover(event) {
  const target = event.target;
  const portrait = target.getAttribute('data-portrait');
  if (!portrait || !portraitVoices[portrait]) return;
  portraitDetails.textContent = portraitVoices[portrait];
}

function resetPortrait() {
  portraitDetails.textContent = 'Approach a portrait in VR to hear its voice.';
}

function updateOnlineStatus() {
  OFFLINE_INDICATOR.textContent = navigator.onLine ? 'Online' : 'Offline-ready';
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

scene.addEventListener('loaded', () => {
  setEchoForm(state.echoForm);
  setHallMode(state.hallMode);
  updateTrees();
  restoreForgeRelics();
  restoreSculptures();
  restoreSoundLoops();
});

forgeCreate.addEventListener('click', createForgeRelic);
forgeClear.addEventListener('click', clearForge);

soundAdd.addEventListener('click', addSoundLoop);
soundToggle.addEventListener('click', toggleAmbience);

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

document.querySelectorAll('.portrait').forEach((portrait) => {
  portrait.addEventListener('mouseenter', handlePortraitHover);
  portrait.addEventListener('mouseleave', resetPortrait);
});

updateOnlineStatus();
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
registerServiceWorker();
