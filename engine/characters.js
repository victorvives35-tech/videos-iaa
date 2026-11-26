// Personajes vectoriales parametrizables.
// character(cfg, st) devuelve un <g> SVG con origen en el centro de la cabeza.
// cfg: { skin, hair, hairColor, shirt, outfit, acc: [...] }
// st:  { mood, mouth (0..1), blink (0..1), tint (0..1), arm (0..1), t }

const INK = "#262833";
const SW = 7; // grosor de contorno

function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const f = (c) => Math.max(0, Math.min(255, Math.round(amt < 0 ? c * (1 + amt) : c + (255 - c) * amt)));
  return "#" + [f(r), f(g), f(b)].map((c) => c.toString(16).padStart(2, "0")).join("");
}
function mix(a, b, k) {
  const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
  const c = [16, 8, 0].map((s) => Math.round(((pa >> s) & 255) * (1 - k) + ((pb >> s) & 255) * k));
  return "#" + c.map((x) => x.toString(16).padStart(2, "0")).join("");
}

const MOODS = {
  //        cejas: ángulo, altura | boca cerrada | ojos (escala vertical)
  neutral: { brow: 0, browY: 0, eye: 1 },
  happy: { brow: -4, browY: -6, eye: 0.85 },
  smug: { brow: 8, browY: 4, eye: 0.6, browAsym: true },
  angry: { brow: 22, browY: 10, eye: 0.8 },
  furious: { brow: 28, browY: 12, eye: 0.7 },
  shocked: { brow: -12, browY: -18, eye: 1.25 },
  sad: { brow: -18, browY: -4, eye: 0.9 },
  worried: { brow: -14, browY: -8, eye: 1.05 },
  pain: { brow: -16, browY: 0, eye: 0.15 },
};

function closedMouth(mood) {
  switch (mood) {
    case "happy": return `<path d="M -36 44 Q 0 86 36 44 Q 0 58 -36 44 Z" fill="#7b2730" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>
      <path d="M -24 48 Q 0 56 24 48 L 22 54 Q 0 60 -22 54 Z" fill="#fff"/>`;
    case "smug": return `<path d="M -26 58 Q 6 66 36 42" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>`;
    case "angry":
    case "furious": return `<path d="M -30 66 Q 0 46 30 66" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>`;
    case "sad": return `<path d="M -24 66 Q 0 52 24 66" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>`;
    case "worried": return `<path d="M -24 60 Q -12 52 0 60 Q 12 68 24 58" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>`;
    case "shocked": return `<ellipse cx="0" cy="60" rx="20" ry="26" fill="#7b2730" stroke="${INK}" stroke-width="6"/>`;
    case "pain": return `<path d="M -30 56 L -18 64 L -6 54 L 6 64 L 18 54 L 30 62" fill="none" stroke="${INK}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>`;
    default: return `<path d="M -22 56 Q 0 64 22 56" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>`;
  }
}

function openMouth(m, mood) {
  const rx = 22 + 10 * m, ry = 6 + 30 * m;
  const cy = 58 + ry * 0.25;
  const angry = mood === "angry" || mood === "furious";
  const top = angry ? `<rect x="${-rx * 0.8}" y="${cy - ry + 1}" width="${rx * 1.6}" height="${Math.min(10, ry * 0.5)}" rx="3" fill="#fff"/>` : `<rect x="${-rx * 0.7}" y="${cy - ry + 1}" width="${rx * 1.4}" height="${Math.min(9, ry * 0.45)}" rx="3" fill="#fff"/>`;
  return `<g>
    <clipPath id="mc${Math.round(m * 1000)}"><ellipse cx="0" cy="${cy}" rx="${rx}" ry="${ry}"/></clipPath>
    <ellipse cx="0" cy="${cy}" rx="${rx}" ry="${ry}" fill="#6d1f2a"/>
    <g clip-path="url(#mc${Math.round(m * 1000)})">
      ${top}
      <ellipse cx="0" cy="${cy + ry * 0.85}" rx="${rx * 0.7}" ry="${ry * 0.55}" fill="#e46a7a"/>
    </g>
    <ellipse cx="0" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="${INK}" stroke-width="6"/>
  </g>`;
}

function eyes(st, mood, cfg) {
  const M = MOODS[mood] || MOODS.neutral;
  const open = Math.max(0.08, (1 - st.blink) * M.eye);
  const look = st.look || 0;
  let s = "";
  for (const side of [-1, 1]) {
    const x = side * 46 + look * 6, y = -2;
    if (mood === "pain" || open < 0.2) {
      s += `<path d="M ${x - 16} ${y} Q ${x} ${y + 8} ${x + 16} ${y}" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>`;
      continue;
    }
    const ry = 21 * open, rx = 15;
    s += `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${INK}"/>`;
    if (open > 0.4) s += `<circle cx="${x + 5}" cy="${y - ry * 0.45}" r="5.5" fill="#fff"/>`;
    // cejas
    const a = (M.brow || 0) * side * (M.browAsym && side < 0 ? -0.6 : 1);
    const by = -52 + (M.browY || 0) + (M.browAsym && side < 0 ? -10 : 0);
    s += `<g transform="translate(${x} ${by}) rotate(${a})"><path d="M -20 0 Q 0 -6 20 0" fill="none" stroke="${cfg.browColor || shade(cfg.hairColor || "#3a2a20", -0.35)}" stroke-width="${cfg.thickBrows ? 13 : 9}" stroke-linecap="round"/></g>`;
  }
  return s;
}

function spikyHair(color, t) {
  const pts = [];
  const n = 9;
  for (let i = 0; i <= n * 2; i++) {
    const a = Math.PI * (1.04 + (0.92 * i) / (n * 2));
    const tip = i % 2 === 1;
    const r = tip ? 190 + ((i * 37) % 23) - (i === n ? -12 : 0) : 120;
    const wob = tip ? Math.sin(t * 2 + i) * 2 : 0;
    pts.push([Math.cos(a) * r + wob, Math.sin(a) * r - 18]);
  }
  let d = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 1; i < pts.length; i++) d += ` L ${pts[i][0]} ${pts[i][1]}`;
  d += ` Q 120 -60 70 -78 Q 20 -60 -20 -86 Q -70 -62 -126 -46 Z`;
  return `<path d="${d}" fill="${color}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
          <path d="M -60 -120 L -40 -150 M 10 -130 L 26 -165" stroke="${shade(color, 0.25)}" stroke-width="7" stroke-linecap="round"/>`;
}

function hairFront(cfg, t) {
  const c = cfg.hairColor || "#3a2a20";
  switch (cfg.hair) {
    case "spiky": return spikyHair(c, t);
    case "bald":
      return `<path d="M -138 -10 Q -150 -70 -112 -92 Q -100 -40 -118 20 Z" fill="${c}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
              <path d="M 138 -10 Q 150 -70 112 -92 Q 100 -40 118 20 Z" fill="${c}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
              <ellipse cx="-40" cy="-100" rx="26" ry="12" fill="#fff" opacity=".55" transform="rotate(-20 -40 -100)"/>`;
    case "short":
      return `<path d="M -134 -6 Q -146 -140 0 -142 Q 146 -140 134 -6 Q 120 -70 60 -84 Q 0 -60 -70 -86 Q -122 -70 -134 -6 Z" fill="${c}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    case "quiff":
      return `<path d="M -134 0 Q -150 -120 -40 -150 Q 60 -210 150 -130 Q 120 -120 128 -60 Q 136 -20 134 0 Q 120 -80 60 -90 Q 0 -70 -60 -90 Q -120 -80 -134 0 Z" fill="${c}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
              <path d="M -10 -150 Q 40 -175 90 -160" fill="none" stroke="${shade(c, 0.3)}" stroke-width="8" stroke-linecap="round"/>`;
    case "bob":
      return `<path d="M -150 70 Q -170 -150 0 -150 Q 170 -150 150 70 L 120 70 Q 128 -40 80 -80 Q 0 -40 -90 -86 Q -128 -40 -120 70 Z" fill="${c}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    case "bun":
      return `<circle cx="0" cy="-160" r="48" fill="${c}" stroke="${INK}" stroke-width="${SW}"/>
              <path d="M -136 10 Q -150 -140 0 -142 Q 150 -140 136 10 Q 126 -70 70 -86 Q 0 -66 -70 -86 Q -126 -70 -136 10 Z" fill="${c}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    case "curly": {
      let s = "";
      for (let i = 0; i < 11; i++) {
        const a = Math.PI * (1.0 + i / 10);
        s += `<circle cx="${Math.cos(a) * 125}" cy="${Math.sin(a) * 118 - 30}" r="40" fill="${c}" stroke="${INK}" stroke-width="${SW}"/>`;
      }
      return s + `<path d="M -110 -60 Q 0 -150 110 -60 Q 0 -100 -110 -60 Z" fill="${c}"/>`;
    }
    default: return "";
  }
}

function hairBack(cfg) {
  const c = cfg.hairColor || "#3a2a20";
  if (cfg.hair === "bob") return `<path d="M -158 150 Q -180 -100 0 -120 Q 180 -100 158 150 Z" fill="${shade(c, -0.15)}" stroke="${INK}" stroke-width="${SW}"/>`;
  if (cfg.hair === "long") return `<path d="M -160 260 Q -190 -120 0 -140 Q 190 -120 160 260 Z" fill="${shade(c, -0.15)}" stroke="${INK}" stroke-width="${SW}"/>`;
  return "";
}

function body(cfg, st) {
  const shirt = cfg.shirt || "#58a6ff";
  const o = cfg.outfit || "shirt";
  const skin = cfg.skin;
  let s = "";
  // cuello
  s += `<rect x="-34" y="96" width="68" height="70" fill="${shade(skin, -0.12)}" stroke="${INK}" stroke-width="${SW}"/>`;
  const torso = `M -160 300 Q -164 170 -60 150 L 60 150 Q 164 170 160 300 L 172 640 L -172 640 Z`;
  if (o === "coat") {
    s += `<path d="${torso}" fill="#f7f9fc" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    s += `<path d="M -60 150 L 0 300 L 60 150 Z" fill="${cfg.shirt || "#9fd3c7"}" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>`;
    if (cfg.acc?.includes("tie")) s += `<path d="M 0 168 L -14 186 L -8 280 L 0 296 L 8 280 L 14 186 Z" fill="${cfg.tie || "#1f8a70"}" stroke="${INK}" stroke-width="5" stroke-linejoin="round"/>`;
    s += `<path d="M -60 150 L -18 300 L -86 250 Z M 60 150 L 18 300 L 86 250 Z" fill="#e8edf3" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>`;
    s += `<rect x="70" y="330" width="58" height="60" rx="8" fill="#e8edf3" stroke="${INK}" stroke-width="5"/>`;
    s += `<path d="M 86 326 L 86 300 M 104 326 L 104 296" stroke="#3b82f6" stroke-width="7" stroke-linecap="round"/>`;
  } else if (o === "apron") {
    s += `<path d="${torso}" fill="${shirt}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    s += `<path d="M -100 220 Q -70 200 -50 160 L 50 160 Q 70 200 100 220 L 110 640 L -110 640 Z" fill="${cfg.apron || "#2e3440"}" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>`;
    s += `<rect x="-60" y="360" width="120" height="70" rx="10" fill="${shade(cfg.apron || "#2e3440", 0.12)}" stroke="${INK}" stroke-width="5"/>`;
    s += `<path d="M -30 360 L -40 320 M 10 360 L 14 318" stroke="#c0c6d0" stroke-width="8" stroke-linecap="round"/>`;
  } else if (o === "uniform") {
    s += `<path d="${torso}" fill="${shirt}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    s += `<path d="M -60 150 L 0 240 L 60 150" fill="#fff" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>`;
    s += `<path d="M -30 176 L 0 210 L 30 176 L 22 168 L 0 190 L -22 168 Z" fill="${cfg.scarf || "#e63946"}" stroke="${INK}" stroke-width="5" stroke-linejoin="round"/>`;
    s += `<rect x="60" y="250" width="60" height="16" rx="5" fill="#f4c430" stroke="${INK}" stroke-width="4"/>`;
    for (const y of [300, 380, 460]) s += `<circle cx="0" cy="${y}" r="8" fill="#f4c430" stroke="${INK}" stroke-width="4"/>`;
  } else if (o === "hoodie") {
    s += `<path d="${torso}" fill="${shirt}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    s += `<path d="M -80 150 Q 0 230 80 150" fill="${shade(shirt, -0.15)}" stroke="${INK}" stroke-width="6"/>`;
    s += `<path d="M -26 200 L -30 290 M 26 200 L 30 290" stroke="#fff" stroke-width="7" stroke-linecap="round"/>`;
    s += `<path d="M -90 420 L 90 420 L 70 520 L -70 520 Z" fill="${shade(shirt, -0.1)}" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>`;
  } else {
    s += `<path d="${torso}" fill="${shirt}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
    s += `<path d="M -60 150 Q 0 205 60 150" fill="${shade(skin, -0.12)}" stroke="${INK}" stroke-width="6"/>`;
  }
  if (cfg.acc?.includes("bib")) {
    s += `<path d="M -110 200 L 110 200 L 120 420 Q 0 440 -120 420 Z" fill="#8fd0ff" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>`;
    s += `<path d="M -110 200 Q -120 170 -60 160 M 110 200 Q 120 170 60 160" fill="none" stroke="#c0c6d0" stroke-width="6" stroke-dasharray="4 8" stroke-linecap="round"/>`;
    s += `<circle cx="-110" cy="204" r="9" fill="#c0c6d0" stroke="${INK}" stroke-width="4"/><circle cx="110" cy="204" r="9" fill="#c0c6d0" stroke="${INK}" stroke-width="4"/>`;
  }
  return s;
}

function arms(cfg, st) {
  const sleeve = cfg.outfit === "coat" ? "#f7f9fc" : cfg.shirt || "#58a6ff";
  const raise = st.arm || 0; // 0 abajo, 1 levantado (puño)
  let s = "";
  for (const side of [-1, 1]) {
    const sx = side * 150, sy = 220;
    const up = side === 1 ? raise : (st.arm2 || 0);
    const ang = -side * (10 + up * 145);
    s += `<g transform="translate(${sx} ${sy}) rotate(${ang})">
      <path d="M -30 0 L 30 0 L 34 250 L -34 250 Z" fill="${sleeve}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
      <circle cx="0" cy="275" r="36" fill="${cfg.skin}" stroke="${INK}" stroke-width="${SW}"/>
    </g>`;
  }
  return s;
}

function accessoriesFront(cfg, st) {
  let s = "";
  const acc = cfg.acc || [];
  if (acc.includes("glasses")) {
    s += `<g fill="rgba(255,255,255,.18)" stroke="${INK}" stroke-width="8">
      <rect x="-86" y="-30" width="78" height="58" rx="16"/><rect x="8" y="-30" width="78" height="58" rx="16"/>
      <path d="M -8 -6 Q 0 -14 8 -6" fill="none"/><path d="M -86 -10 L -128 -18 M 86 -10 L 128 -18" fill="none"/></g>`;
  }
  if (acc.includes("mustache")) {
    s += `<path d="M -50 40 Q -26 20 0 34 Q 26 20 50 40 Q 30 52 0 44 Q -30 52 -50 40 Z" fill="${shade(cfg.hairColor || "#555", -0.2)}" stroke="${INK}" stroke-width="5" stroke-linejoin="round"/>`;
  }
  if (acc.includes("beard")) {
    s += `<path d="M -120 20 Q -110 150 0 160 Q 110 150 120 20 Q 100 90 50 80 Q 0 70 -50 80 Q -100 90 -120 20 Z" fill="${cfg.hairColor || "#3a2a20"}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>`;
  }
  if (acc.includes("mask")) {
    const k = 1 + (st.mouth || 0) * 0.08;
    s += `<g transform="translate(0 64) scale(1 ${k}) translate(0 -64)">
      <path d="M -126 6 L -98 20 M 126 6 L 98 20" stroke="#dbe6ee" stroke-width="7" stroke-linecap="round"/>
      <path d="M -100 18 Q 0 4 100 18 L 96 92 Q 0 128 -96 92 Z" fill="#8ccaf0" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
      <path d="M -88 44 Q 0 34 88 44 M -86 68 Q 0 60 86 68" fill="none" stroke="#5ea9d6" stroke-width="5" stroke-linecap="round"/></g>`;
  }
  if (acc.includes("headmirror")) {
    s += `<path d="M -132 -66 Q 0 -118 132 -66" fill="none" stroke="#3b4252" stroke-width="12"/>
      <circle cx="0" cy="-112" r="34" fill="#e8eef5" stroke="${INK}" stroke-width="${SW}"/><circle cx="0" cy="-112" r="12" fill="#262833"/>
      <path d="M -16 -128 Q -6 -136 6 -132" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>`;
  }
  if (acc.includes("captainhat")) {
    s += `<path d="M -120 -96 Q 0 -200 120 -96 Z" fill="${cfg.hat || "#1d3557"}" stroke="${INK}" stroke-width="${SW}" stroke-linejoin="round"/>
      <path d="M -132 -90 Q 0 -110 132 -90 L 126 -70 Q 0 -86 -126 -70 Z" fill="#111827" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>
      <circle cx="0" cy="-130" r="14" fill="#f4c430" stroke="${INK}" stroke-width="5"/>`;
  }
  if (acc.includes("smallhat")) {
    s += `<path d="M -70 -120 Q 0 -170 70 -120 L 64 -96 Q 0 -110 -64 -96 Z" fill="${cfg.hat || "#e63946"}" stroke="${INK}" stroke-width="6" stroke-linejoin="round" transform="rotate(-10)"/>`;
  }
  if (acc.includes("headphones")) {
    s += `<path d="M -140 0 Q -150 -170 0 -170 Q 150 -170 140 0" fill="none" stroke="#2b2d42" stroke-width="16"/>
      <rect x="-166" y="-30" width="40" height="70" rx="16" fill="#ef476f" stroke="${INK}" stroke-width="6"/>
      <rect x="126" y="-30" width="40" height="70" rx="16" fill="#ef476f" stroke="${INK}" stroke-width="6"/>`;
  }
  return s;
}

function character(cfg, st) {
  const mood = st.mood || "neutral";
  const baseSkin = cfg.skin || "#f8c9a0";
  const tint = st.tint || 0;
  const skin = mix(baseSkin, "#e8554e", tint * 0.75);
  const c = Object.assign({}, cfg, { skin });
  const masked = (cfg.acc || []).includes("mask");
  let s = `<g>`;
  s += hairBack(c);
  s += `<g>${body(c, st)}</g>`;
  s += arms(c, st);
  // cabeza
  s += `<ellipse cx="-134" cy="10" rx="24" ry="30" fill="${skin}" stroke="${INK}" stroke-width="${SW}"/>`;
  s += `<ellipse cx="134" cy="10" rx="24" ry="30" fill="${skin}" stroke="${INK}" stroke-width="${SW}"/>`;
  s += `<path d="M -138 0 Q -140 -130 0 -132 Q 140 -130 138 0 Q 136 118 0 122 Q -136 118 -138 0 Z" fill="${skin}" stroke="${INK}" stroke-width="${SW}"/>`;
  s += `<ellipse cx="-80" cy="38" rx="24" ry="13" fill="#ff8a8a" opacity="${0.45 + tint * 0.3}"/>`;
  s += `<ellipse cx="80" cy="38" rx="24" ry="13" fill="#ff8a8a" opacity="${0.45 + tint * 0.3}"/>`;
  s += eyes(st, mood, c);
  s += `<path d="M -8 22 Q 2 32 12 20" fill="none" stroke="${shade(skin, -0.3)}" stroke-width="6" stroke-linecap="round"/>`;
  if (!masked) {
    const m = st.mouth || 0;
    s += m > 0.06 ? openMouth(m, mood) : closedMouth(mood);
  }
  s += hairFront(c, st.t || 0);
  s += accessoriesFront(c, st);
  s += `</g>`;
  return s;
}

window.character = character;
window.shade = shade;
window.INK = INK;
