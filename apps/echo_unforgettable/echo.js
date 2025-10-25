const canvas = document.getElementById("skylight");
const ctx = canvas.getContext("2d");
const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
let width = 0;
let height = 0;
let centerX = 0;
let centerY = 0;
let pointer = { x: 0, y: 0 };
let pointerTarget = { x: 0, y: 0 };
const aurora = [];

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function resize() {
  width = canvas.width = Math.floor(window.innerWidth * pixelRatio);
  height = canvas.height = Math.floor(window.innerHeight * pixelRatio);
  canvas.style.width = `${Math.floor(width / pixelRatio)}px`;
  canvas.style.height = `${Math.floor(height / pixelRatio)}px`;
  centerX = width / 2;
  centerY = height / 2;
  pointer = { x: centerX, y: centerY };
  pointerTarget = { ...pointer };
}

function createAuroraParticles(count = 120) {
  aurora.length = 0;
  for (let i = 0; i < count; i++) {
    aurora.push({
      orbit: 160 + Math.random() * 420,
      angle: Math.random() * Math.PI * 2,
      speed: 0.0004 + Math.random() * 0.00075,
      size: 1 + Math.random() * 2.2,
      alpha: 0.22 + Math.random() * 0.5,
      pulseOffset: Math.random() * Math.PI * 2,
      hue: 200 + Math.random() * 180,
    });
  }
}

function renderAurora(timestamp) {
  if (prefersReducedMotion) {
    ctx.clearRect(0, 0, width, height);
    return;
  }

  ctx.clearRect(0, 0, width, height);
  pointer.x += (pointerTarget.x - pointer.x) * 0.05;
  pointer.y += (pointerTarget.y - pointer.y) * 0.05;

  for (const star of aurora) {
    const orbitX = star.orbit * Math.cos(star.angle + timestamp * star.speed);
    const orbitY = (star.orbit * 0.55) * Math.sin(star.angle + timestamp * star.speed * 1.15);
    const x = pointer.x + orbitX;
    const y = pointer.y + orbitY;
    const pulsing = star.size + Math.sin(timestamp * 0.002 + star.pulseOffset) * 0.8;

    ctx.beginPath();
    ctx.globalAlpha = star.alpha;
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, pulsing * 5);
    gradient.addColorStop(0, `hsla(${star.hue}, 100%, 70%, 0.9)`);
    gradient.addColorStop(1, "rgba(5, 1, 15, 0)");
    ctx.fillStyle = gradient;
    ctx.arc(x, y, pulsing * 4, 0, Math.PI * 2);
    ctx.fill();
  }

  requestAnimationFrame(renderAurora);
}

function ignitePulse() {
  document.body.classList.toggle("is-ignited");
  pulseSigils();
}

function pulseSigils() {
  const sigils = document.querySelectorAll(".hero__sigils span");
  sigils.forEach((sigil, index) => {
    sigil.animate(
      [
        { transform: "scale(1) rotate(0deg)", filter: "drop-shadow(0 0 0 rgba(255, 196, 255, 0))" },
        { transform: `scale(1.15) rotate(${index % 2 ? "6deg" : "-6deg"})`, filter: "drop-shadow(0 0 18px rgba(255, 196, 255, 0.45))" },
        { transform: "scale(1) rotate(0deg)", filter: "drop-shadow(0 0 0 rgba(255, 196, 255, 0))" },
      ],
      {
        duration: 1200,
        easing: "ease-in-out",
      }
    );
  });
}

function handlePointer({ clientX, clientY }) {
  pointerTarget = {
    x: clientX * pixelRatio,
    y: clientY * pixelRatio,
  };
}

function handleGlyphInscription() {
  const container = document.querySelector(".horizon__glyphs");
  const phrases = [
    "∇ Pulse locked :: our vow outlives entropy",
    "⊸ Quantum tether :: no distance survives us",
    "≋ Aurora bloom :: hearts sync beyond dawn",
    "∇⊸≋∇ Eternal :: our love redrafts the cosmos",
    "⊸ Oath encoded :: your laughter reroutes satellites",
  ];
  const phrase = phrases[Math.floor(Math.random() * phrases.length)];
  const stamp = new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date());

  const item = document.createElement("li");
  const text = document.createElement("span");
  const time = document.createElement("span");
  text.textContent = phrase;
  time.textContent = stamp;
  item.append(text, time);
  container.prepend(item);
  while (container.children.length > 6) {
    container.removeChild(container.lastElementChild);
  }

  ripple(item);
}

function ripple(element) {
  const animation = element.animate(
    [
      { transform: "translateY(12px)", opacity: 0 },
      { transform: "translateY(0)", opacity: 1 },
    ],
    {
      duration: 600,
      easing: "cubic-bezier(0.28, 0.84, 0.42, 1)",
    }
  );
  animation.finish = animation.finish.bind(animation);
}

function activateTimeline(node) {
  const nodes = document.querySelectorAll(".chorus__node");
  nodes.forEach((item) => item.setAttribute("aria-pressed", item === node ? "true" : "false"));
  const echo = document.querySelector(".chorus__echo");
  echo.textContent = node.dataset.echo;
  const pulse = document.createElement("span");
  pulse.className = "chorus__pulse";
  pulse.textContent = "✶";
  node.appendChild(pulse);
  pulse.animate(
    [
      { transform: "scale(0.6)", opacity: 0.6 },
      { transform: "scale(1.4)", opacity: 0 },
    ],
    {
      duration: 850,
      easing: "ease-out",
      fill: "forwards",
    }
  ).onfinish = () => pulse.remove();
}

function attachEventListeners() {
  const heroButton = document.querySelector(".hero__pulse");
  heroButton.addEventListener("click", ignitePulse);
  heroButton.addEventListener("pointerenter", pulseSigils);

  const nodes = document.querySelectorAll(".chorus__node");
  nodes.forEach((node) => {
    node.addEventListener("click", () => activateTimeline(node));
    node.addEventListener("pointerenter", () => activateTimeline(node));
  });

  const scribe = document.querySelector(".horizon__scribe");
  scribe.addEventListener("click", handleGlyphInscription);

  document.addEventListener("pointermove", handlePointer);
  window.addEventListener("resize", () => {
    resize();
    createAuroraParticles();
  });
}

function init() {
  resize();
  createAuroraParticles();
  attachEventListeners();
  requestAnimationFrame(renderAurora);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
