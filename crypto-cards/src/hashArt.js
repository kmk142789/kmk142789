function makePRNG(hex) {
  let seed = parseInt(hex.slice(0, 8), 16) || 0x12345678;
  return function rand() {
    seed ^= seed << 13;
    seed ^= seed >>> 17;
    seed ^= seed << 5;
    return (seed >>> 0) / 0xffffffff;
  };
}

export function pickColorsFromHash(hash) {
  const r = makePRNG(hash);
  const h1 = Math.floor(r() * 360);
  const h2 = (h1 + 120 + Math.floor(r() * 30) - 15) % 360;
  const h3 = (h1 + 240 + Math.floor(r() * 30) - 15) % 360;
  const s1 = 55 + Math.floor(r() * 35);
  const s2 = 55 + Math.floor(r() * 35);
  const s3 = 55 + Math.floor(r() * 35);
  const l1 = 45 + Math.floor(r() * 10);
  const l2 = 45 + Math.floor(r() * 10);
  const l3 = 45 + Math.floor(r() * 10);
  return [
    `hsl(${h1}deg ${s1}% ${l1}%)`,
    `hsl(${h2}deg ${s2}% ${l2}%)`,
    `hsl(${h3}deg ${s3}% ${l3}%)`,
  ];
}

export function titleFromHash(hash) {
  const nouns = [
    "Cipher",
    "Relic",
    "Sigil",
    "Obelisk",
    "Shard",
    "Beacon",
    "Bloom",
    "Warden",
    "Seraph",
    "Rift",
    "Spire",
    "Helix",
    "Grail",
    "Totem",
    "Eclipse",
    "Nova",
    "Catalyst",
    "Vector",
  ];
  const adjs = [
    "Genesis",
    "Abyssal",
    "Volt",
    "Mythic",
    "Glacial",
    "Solar",
    "Quantum",
    "Echoing",
    "Fractal",
    "Nebular",
    "Prismatic",
  ];
  const i = parseInt(hash.slice(8, 12), 16);
  const j = parseInt(hash.slice(12, 16), 16);
  return `${adjs[i % adjs.length]} ${nouns[j % nouns.length]}`;
}

export function hashArtDataUrl(hash, { width = 480, height = 672, palette } = {}) {
  const cnv = document.createElement("canvas");
  cnv.width = width;
  cnv.height = height;
  const ctx = cnv.getContext("2d");
  const rnd = makePRNG(hash);
  const [c1, c2, c3] = palette || pickColorsFromHash(hash);

  const g = ctx.createLinearGradient(0, 0, width, height);
  g.addColorStop(0, c1);
  g.addColorStop(0.5, c2);
  g.addColorStop(1, c3);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, width, height);

  const img = ctx.createImageData(width, height);
  const data = img.data;

  const fx = 0.004 + rnd() * 0.01;
  const fy = 0.004 + rnd() * 0.01;
  const fz = 0.004 + rnd() * 0.01;
  const p1 = rnd() * Math.PI * 2;
  const p2 = rnd() * Math.PI * 2;
  const p3 = rnd() * Math.PI * 2;

  const rgb1 = hslToRgb(c1);
  const rgb2 = hslToRgb(c2);
  const rgb3 = hslToRgb(c3);

  for (let y = 0; y < height; y++) {
    const sy = Math.sin(y * fy + p2);
    const sz = Math.sin(y * fz + p3);
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const s = Math.sin(x * fx + p1) + sy + sz;
      const t = (s + 3) / 6;
      const r = lerp3(rgb1[0], rgb2[0], rgb3[0], t);
      const g = lerp3(rgb1[1], rgb2[1], rgb3[1], t);
      const b = lerp3(rgb1[2], rgb2[2], rgb3[2], t);
      data[i + 0] = r;
      data[i + 1] = g;
      data[i + 2] = b;
      data[i + 3] = 255;
    }
  }
  ctx.globalAlpha = 0.35;
  ctx.putImageData(img, 0, 0);
  ctx.globalAlpha = 1;

  const vg = ctx.createRadialGradient(
    width / 2,
    height * 0.45,
    Math.min(width, height) * 0.1,
    width / 2,
    height / 2,
    Math.max(width, height) * 0.75
  );
  vg.addColorStop(0, "rgba(0,0,0,0)");
  vg.addColorStop(1, "rgba(0,0,0,0.45)");
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, width, height);

  return cnv.toDataURL("image/png");
}

function lerp(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function lerp3(a, b, c, t) {
  return t < 0.5 ? lerp(a, b, t * 2) : lerp(b, c, (t - 0.5) * 2);
}

function hslToRgb(hsl) {
  const c = document.createElement("canvas");
  const x = c.getContext("2d");
  x.fillStyle = hsl;
  x.fillRect(0, 0, 1, 1);
  const [r, g, b] = x.getImageData(0, 0, 1, 1).data;
  return [r, g, b];
}
