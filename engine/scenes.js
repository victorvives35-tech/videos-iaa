// Escenarios a pantalla completa (1080x1920). Cada escena define fondo, primer plano
// y la posición/escala de cada personaje (centro de la cabeza).

const W = 1080, H = 1920;

function wallGrad(id, a, b) {
  return `<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>`;
}
function softShadow(cx, cy, rx, ry, o = 0.18) {
  return `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#000" opacity="${o}"/>`;
}
function tooth(x, y, s, fill = "#fff") {
  return `<path transform="translate(${x} ${y}) scale(${s})" d="M -30 -34 Q -44 -34 -44 -14 Q -44 8 -34 28 L -26 56 Q -22 64 -16 56 L -8 22 Q 0 14 8 22 L 16 56 Q 22 64 26 56 L 34 28 Q 44 8 44 -14 Q 44 -34 30 -34 Q 18 -34 0 -26 Q -18 -34 -30 -34 Z" fill="${fill}" stroke="${INK}" stroke-width="${6 / s}" stroke-linejoin="round"/>`;
}

const SCENES = {
  dentista: {
    pos: { yo: { x: 330, y: 1130, s: 1.08 }, otro: { x: 800, y: 1000, s: 1.12 } },
    bg: (t) => `
      <defs>${wallGrad("wall", "#e3f6f1", "#bfe6dc")}</defs>
      <rect width="${W}" height="${H}" fill="url(#wall)"/>
      <rect y="1230" width="${W}" height="${H - 1230}" fill="#9fd6c8"/>
      <rect y="1222" width="${W}" height="16" fill="#7cc2b1"/>
      <!-- póster diente -->
      <g transform="translate(70 560) rotate(-3)">
        <rect width="220" height="280" rx="14" fill="#fff" stroke="${INK}" stroke-width="7"/>
        <rect x="14" y="14" width="192" height="40" rx="8" fill="#ffd6dc"/>
        <text x="110" y="44" font-family="Fredoka" font-size="28" text-anchor="middle" fill="#d6336c">¡CEPÍLLATE!</text>
        ${tooth(110, 170, 1.9)}
        <path d="M 72 150 Q 82 140 92 150" stroke="${INK}" stroke-width="5" fill="none" stroke-linecap="round"/>
        <path d="M 128 150 Q 138 140 148 150" stroke="${INK}" stroke-width="5" fill="none" stroke-linecap="round"/>
        <path d="M 92 180 Q 110 196 128 180" stroke="${INK}" stroke-width="5" fill="none" stroke-linecap="round"/>
      </g>
      <!-- negatoscopio -->
      <g transform="translate(620 440)">
        <rect width="400" height="300" rx="16" fill="#2b3a4a" stroke="${INK}" stroke-width="8"/>
        <rect x="18" y="18" width="364" height="264" rx="8" fill="#1b2633"/>
        ${[0, 1, 2, 3, 4].map((i) => tooth(64 + i * 68, 90, 0.62, "#e9f4ff")).join("")}
        ${[0, 1, 2, 3, 4].map((i) => `<g transform="translate(${64 + i * 68} 210) scale(1 -1)">${tooth(0, 0, 0.62, "#e9f4ff")}</g>`).join("")}
        <circle cx="370" cy="30" r="7" fill="#7CFF9B" opacity="${0.6 + 0.4 * Math.sin(t * 3)}"/>
      </g>
      <!-- lámpara -->
      <g transform="translate(250 0)">
        <rect x="-10" y="0" width="20" height="200" fill="#9aa5b1" stroke="${INK}" stroke-width="6"/>
        <path d="M -150 200 Q 0 140 150 200 L 130 250 Q 0 210 -130 250 Z" fill="#f2f4f7" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>
        <ellipse cx="0" cy="246" rx="120" ry="18" fill="#fff8c4" stroke="${INK}" stroke-width="5"/>
        <path d="M -120 252 L -260 640 L 260 640 L 120 252 Z" fill="#fff9c9" opacity=".12"/>
      </g>
      <!-- sillón -->
      <rect x="110" y="850" width="440" height="980" rx="120" fill="#2aa198" stroke="${INK}" stroke-width="8"/>
      <rect x="150" y="880" width="360" height="230" rx="80" fill="#35b5aa"/>
      ${softShadow(800, 1600, 260, 40, 0.12)}
    `,
    fg: (t) => `
      <rect x="-20" y="1560" width="${W + 40}" height="400" rx="0" fill="#e9eef2" stroke="${INK}" stroke-width="8"/>
      <rect x="-20" y="1560" width="${W + 40}" height="30" fill="#d6dde3"/>
      <!-- bandeja -->
      <rect x="120" y="1500" width="360" height="40" rx="12" fill="#c7d0d9" stroke="${INK}" stroke-width="6"/>
      <path d="M 170 1500 L 230 1440 M 260 1500 L 300 1420 M 340 1500 L 400 1450" stroke="#7b8794" stroke-width="10" stroke-linecap="round"/>
      <circle cx="300" cy="1418" r="10" fill="#e9eef2" stroke="${INK}" stroke-width="5"/>
      <!-- vaso -->
      <path d="M 880 1420 L 980 1420 L 966 1556 L 894 1556 Z" fill="#d7f0ff" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>
      <path d="M 886 1470 L 974 1470 L 966 1556 L 894 1556 Z" fill="#7cc8f7" opacity=".8"/>
    `,
  },

  peluqueria: {
    pos: { yo: { x: 330, y: 1140, s: 1.08 }, otro: { x: 800, y: 995, s: 1.12 } },
    bg: (t) => `
      <defs>${wallGrad("wall2", "#fff1de", "#ffe2bf")}
        <pattern id="stripes" width="80" height="80" patternUnits="userSpaceOnUse"><rect width="40" height="80" fill="#ffe7c7"/></pattern></defs>
      <rect width="${W}" height="${H}" fill="url(#wall2)"/>
      <rect width="${W}" height="1200" fill="url(#stripes)" opacity=".6"/>
      <rect y="1200" width="${W}" height="${H - 1200}" fill="#3d3d4e"/>
      ${Array.from({ length: 14 }, (_, i) => `<rect x="${i * 80}" y="1200" width="40" height="40" fill="#f4f4f4"/><rect x="${i * 80 + 40}" y="1240" width="40" height="40" fill="#f4f4f4"/>`).join("")}
      <!-- espejo con bombillas -->
      <g transform="translate(560 380)">
        <rect width="460" height="560" rx="30" fill="#9c6b3f" stroke="${INK}" stroke-width="8"/>
        <rect x="30" y="30" width="400" height="500" rx="18" fill="#cfeaf5" stroke="${INK}" stroke-width="6"/>
        <path d="M 80 80 L 200 40 M 90 160 L 300 80" stroke="#fff" stroke-width="16" opacity=".6" stroke-linecap="round"/>
        ${[0, 1, 2, 3, 4].map((i) => `<circle cx="${60 + i * 85}" cy="15" r="18" fill="#fff6b0" stroke="${INK}" stroke-width="5" opacity="${0.75 + 0.25 * Math.sin(t * 4 + i)}"/>`).join("")}
      </g>
      <!-- poste de barbero -->
      <g transform="translate(110 420)">
        <rect x="-14" y="-30" width="108" height="30" rx="10" fill="#d0d5dd" stroke="${INK}" stroke-width="6"/>
        <clipPath id="pole"><rect x="0" y="0" width="80" height="320" rx="30"/></clipPath>
        <rect x="0" y="0" width="80" height="320" rx="30" fill="#fff"/>
        <g clip-path="url(#pole)">${Array.from({ length: 10 }, (_, i) => `<path d="M -40 ${i * 70 - 140 + ((t * 60) % 70)} L 120 ${i * 70 - 220 + ((t * 60) % 70)} L 120 ${i * 70 - 190 + ((t * 60) % 70)} L -40 ${i * 70 - 110 + ((t * 60) % 70)} Z" fill="${i % 2 ? "#e63946" : "#3a86ff"}"/>`).join("")}</g>
        <rect x="0" y="0" width="80" height="320" rx="30" fill="none" stroke="${INK}" stroke-width="7"/>
        <rect x="-14" y="320" width="108" height="30" rx="10" fill="#d0d5dd" stroke="${INK}" stroke-width="6"/>
      </g>
      <!-- sillón -->
      <rect x="120" y="860" width="420" height="960" rx="70" fill="#c1121f" stroke="${INK}" stroke-width="8"/>
      <rect x="160" y="890" width="340" height="210" rx="60" fill="#d62839"/>
      ${softShadow(800, 1600, 260, 40, 0.12)}
    `,
    fg: (t) => `
      <rect x="-20" y="1560" width="${W + 40}" height="400" fill="#f7f1e8" stroke="${INK}" stroke-width="8"/>
      <rect x="-20" y="1560" width="${W + 40}" height="30" fill="#e8dfd2"/>
      <!-- tijeras y peine -->
      <g transform="translate(240 1500) rotate(-20)">
        <circle cx="-40" cy="20" r="22" fill="none" stroke="${INK}" stroke-width="9"/><circle cx="10" cy="34" r="22" fill="none" stroke="${INK}" stroke-width="9"/>
        <path d="M -24 6 L 90 -50 M -4 16 L 96 -30" stroke="#aab4c0" stroke-width="12" stroke-linecap="round"/>
      </g>
      <rect x="380" y="1520" width="180" height="34" rx="8" fill="#2b2d42" stroke="${INK}" stroke-width="5"/>
      ${Array.from({ length: 12 }, (_, i) => `<rect x="${392 + i * 14}" y="1500" width="6" height="22" fill="#2b2d42"/>`).join("")}
      <!-- spray -->
      <rect x="880" y="1420" width="90" height="140" rx="18" fill="#4cc9f0" stroke="${INK}" stroke-width="7"/>
      <rect x="900" y="1380" width="50" height="44" rx="6" fill="#f72585" stroke="${INK}" stroke-width="6"/>
    `,
  },

  avion: {
    pos: { yo: { x: 330, y: 1140, s: 1.08 }, otro: { x: 800, y: 995, s: 1.12 } },
    bg: (t) => `
      <defs>${wallGrad("cab", "#f5f2ea", "#e6e0d2")}${wallGrad("sky", "#7cc6ff", "#c9ecff")}</defs>
      <rect width="${W}" height="${H}" fill="url(#cab)"/>
      <!-- portaequipajes -->
      <path d="M 0 0 L ${W} 0 L ${W} 300 Q 540 360 0 300 Z" fill="#dcd6c8" stroke="${INK}" stroke-width="8"/>
      <path d="M 0 250 Q 540 310 ${W} 250" fill="none" stroke="#b9b2a2" stroke-width="6"/>
      ${[160, 540, 920].map((x) => `<rect x="${x - 50}" y="270" width="100" height="22" rx="8" fill="#b9b2a2"/>`).join("")}
      <!-- ventanillas -->
      ${[90, 470, 850].map((x) => `<g transform="translate(${x} 470)">
        <rect width="150" height="220" rx="70" fill="#cfc8b8" stroke="${INK}" stroke-width="7"/>
        <clipPath id="win${x}"><rect x="18" y="18" width="114" height="184" rx="56"/></clipPath>
        <rect x="18" y="18" width="114" height="184" rx="56" fill="url(#sky)"/>
        <g clip-path="url(#win${x})">
          <g transform="translate(${((-t * 120 + x * 3) % 300) + 200} 0)"><ellipse cx="0" cy="120" rx="60" ry="24" fill="#fff"/><ellipse cx="-30" cy="104" rx="36" ry="24" fill="#fff"/></g>
          <g transform="translate(${((-t * 80 + x * 7) % 400) + 280} 0)"><ellipse cx="0" cy="60" rx="40" ry="14" fill="#fff" opacity=".8"/></g>
        </g>
        <rect x="18" y="18" width="114" height="184" rx="56" fill="none" stroke="${INK}" stroke-width="5"/>
      </g>`).join("")}
      <rect y="1220" width="${W}" height="${H - 1220}" fill="#4a4e69"/>
      <!-- asiento -->
      <rect x="120" y="850" width="420" height="980" rx="90" fill="#1d4e89" stroke="${INK}" stroke-width="8"/>
      <rect x="160" y="870" width="340" height="140" rx="50" fill="#e9ecef" stroke="${INK}" stroke-width="6"/>
      <rect x="160" y="1030" width="340" height="700" rx="60" fill="#2463a8"/>
      ${softShadow(800, 1600, 260, 40, 0.12)}
    `,
    fg: (t) => `
      <rect x="-20" y="1560" width="${W + 40}" height="400" fill="#d9d4c7" stroke="${INK}" stroke-width="8"/>
      <rect x="-20" y="1560" width="${W + 40}" height="30" fill="#c4bdac"/>
      <!-- carrito -->
      <rect x="760" y="1380" width="300" height="180" rx="14" fill="#adb5bd" stroke="${INK}" stroke-width="7"/>
      <rect x="780" y="1400" width="260" height="60" rx="8" fill="#ced4da"/>
      <rect x="800" y="1330" width="44" height="60" rx="6" fill="#e63946" stroke="${INK}" stroke-width="5"/>
      <rect x="860" y="1340" width="44" height="50" rx="6" fill="#f4a261" stroke="${INK}" stroke-width="5"/>
      <!-- vaso -->
      <path d="M 200 1460 L 280 1460 L 270 1556 L 210 1556 Z" fill="#fff" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>
      <path d="M 204 1490 L 276 1490 L 270 1556 L 210 1556 Z" fill="#ffb703"/>
    `,
  },

  salon: {
    pos: { yo: { x: 330, y: 1130, s: 1.08 }, otro: { x: 800, y: 1000, s: 1.12 } },
    bg: (t) => `
      <defs>${wallGrad("wall4", "#efe9ff", "#d9cffc")}</defs>
      <rect width="${W}" height="${H}" fill="url(#wall4)"/>
      <rect y="1230" width="${W}" height="${H - 1230}" fill="#b8a9e8"/>
      <g transform="translate(620 420)"><rect width="380" height="300" rx="14" fill="#fff" stroke="${INK}" stroke-width="8"/>
        <rect x="20" y="20" width="340" height="260" fill="#a0e7e5"/><circle cx="270" cy="90" r="34" fill="#ffd166"/>
        <path d="M 20 280 L 140 140 L 230 240 L 280 190 L 360 280 Z" fill="#06d6a0" stroke="${INK}" stroke-width="5" stroke-linejoin="round"/></g>
      <rect x="120" y="860" width="420" height="960" rx="90" fill="#ff7b54" stroke="${INK}" stroke-width="8"/>
    `,
    fg: (t) => `<rect x="-20" y="1560" width="${W + 40}" height="400" fill="#fdfdfd" stroke="${INK}" stroke-width="8"/>`,
  },

  noche_electoral: {
    pos: { yo: { x: 320, y: 1150, s: 1.08 }, otro: { x: 790, y: 1010, s: 1.12 } },
    bg: (t) => {
      const bars = [["#2f9e44", 0.92, "1º"], ["#1c7ed6", 0.7, "2º"], ["#e03131", 0.62, "3º"], ["#ae3ec9", 0.3, "4º"]];
      const grow = Math.min(1, t / 2.5);
      return `
      <defs>${wallGrad("wall5", "#2b2f55", "#3d3a6b")}${wallGrad("scr", "#0b1d3a", "#14325f")}</defs>
      <rect width="${W}" height="${H}" fill="url(#wall5)"/>
      <rect y="1240" width="${W}" height="${H - 1240}" fill="#5a4a78"/>
      <!-- ventana nocturna -->
      <g transform="translate(40 300)">
        <rect width="300" height="380" rx="12" fill="#13163a" stroke="${INK}" stroke-width="8"/>
        ${[[60, 80], [200, 60], [130, 160], [240, 220], [80, 260]].map(([x, y], i) => `<circle cx="${x}" cy="${y}" r="${3 + (i % 2) * 2}" fill="#fff" opacity="${0.5 + 0.5 * Math.sin(t * 3 + i)}"/>`).join("")}
        <circle cx="220" cy="110" r="36" fill="#ffe8a3"/><circle cx="236" cy="100" r="34" fill="#13163a"/>
        <path d="M 0 380 L 0 300 L 50 300 L 50 260 L 110 260 L 110 320 L 160 320 L 160 240 L 230 240 L 230 290 L 300 290 L 300 380 Z" fill="#0a0c24"/>
        ${[[70, 280], [130, 335], [185, 260], [250, 310]].map(([x, y], i) => `<rect x="${x}" y="${y}" width="14" height="18" fill="#ffd43b" opacity="${(Math.floor(t * 0.7 + i) % 3) ? 0.9 : 0.2}"/>`).join("")}
        <path d="M 150 0 L 150 380 M 0 190 L 300 190" stroke="${INK}" stroke-width="8"/>
      </g>
      <!-- televisión con resultados -->
      <g transform="translate(470 340)">
        <rect x="-16" y="-16" width="602" height="392" rx="22" fill="#1b1d26" stroke="${INK}" stroke-width="8"/>
        <rect width="570" height="360" rx="10" fill="url(#scr)"/>
        <rect x="0" y="0" width="570" height="54" fill="#e03131"/>
        <text x="20" y="38" font-family="Fredoka" font-size="30" fill="#fff">ELECCIONES GENERALES</text>
        <circle cx="530" cy="27" r="9" fill="#fff" opacity="${0.4 + 0.6 * (Math.floor(t * 2) % 2)}"/>
        ${bars.map(([c, v, l], i) => `<rect x="${60 + i * 125}" y="${330 - 240 * v * grow}" width="90" height="${240 * v * grow}" rx="6" fill="${c}" stroke="#fff" stroke-width="3"/>
          <text x="${105 + i * 125}" y="${320 - 240 * v * grow}" font-family="Fredoka" font-size="26" fill="#fff" text-anchor="middle">${l}</text>`).join("")}
        <rect x="200" y="380" width="170" height="60" fill="#1b1d26" stroke="${INK}" stroke-width="7"/>
      </g>
      <!-- sofá -->
      <rect x="60" y="900" width="540" height="900" rx="110" fill="#e8590c" stroke="${INK}" stroke-width="8"/>
      <rect x="110" y="940" width="440" height="230" rx="70" fill="#f76707"/>
      ${softShadow(790, 1610, 260, 40, 0.15)}
    `;
    },
    fg: (t) => `
      <!-- mesa con palomitas y mando -->
      <rect x="120" y="1530" width="300" height="40" rx="10" fill="#1b1d26" stroke="${INK}" stroke-width="6"/>
      <path d="M 170 1530 L 190 1440 L 290 1440 L 310 1530 Z" fill="#fff" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/>
      <path d="M 200 1440 L 205 1530 M 240 1440 L 240 1530 M 280 1440 L 275 1530" stroke="#e03131" stroke-width="12"/>
      ${[[200, 1430], [230, 1418], [260, 1426], [285, 1434], [245, 1404]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="16" fill="#fff4c2" stroke="${INK}" stroke-width="4"/>`).join("")}
      <rect x="860" y="1500" width="120" height="50" rx="14" fill="#343a40" stroke="${INK}" stroke-width="6"/>
      <circle cx="890" cy="1525" r="8" fill="#e03131"/><circle cx="930" cy="1525" r="6" fill="#adb5bd"/><circle cx="955" cy="1525" r="6" fill="#adb5bd"/>
    `,
  },
};

function cabinet(top, color, handle = "#c9d2dc") {
  const c2 = shade(color, -0.12);
  let s = `<rect x="-20" y="${top}" width="1120" height="${1960 - top}" fill="${color}" stroke="${INK}" stroke-width="8"/>`;
  s += `<rect x="-20" y="${top}" width="1120" height="34" fill="${shade(color, 0.25)}" stroke="${INK}" stroke-width="8"/>`;
  for (const x of [40, 400, 760]) {
    s += `<rect x="${x}" y="${top + 70}" width="300" height="${1920 - top - 110}" rx="18" fill="${c2}" stroke="${INK}" stroke-width="6"/>`;
    s += `<rect x="${x + 110}" y="${top + 100}" width="80" height="18" rx="9" fill="${handle}" stroke="${INK}" stroke-width="5"/>`;
  }
  return s;
}
SCENES.peluqueria.cabinet = "#a8743f";
SCENES.avion.cabinet = "#c4bdac";
SCENES.noche_electoral.cabinet = "#7a5230";
for (const [k, sc] of Object.entries(SCENES)) {
  const fg = sc.fg, col = sc.cabinet || "#e9eef2";
  sc.fg = (t) => `<g transform="translate(0 100)">${fg(t)}</g>` + cabinet(1690, col);
}
window.SCENES = SCENES;
window.tooth = tooth;
