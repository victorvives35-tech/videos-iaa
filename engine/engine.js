// Motor de render determinista: renderAt(t) dibuja el fotograma del instante t.
let TL = null;

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const easeOutCubic = (x) => 1 - Math.pow(1 - clamp(x), 3);
const easeInOut = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const easeOutBack = (x) => { x = clamp(x); const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const TIP_COLORS = ["#2a9d8f", "#f4a261", "#8e5cf7", "#3a86ff", "#ef476f", "#06a77d", "#ff7b00"];
const tipColor = (tip) => (tip.kind === "extra" ? "#e63946" : TIP_COLORS[(tip.n - 1) % TIP_COLORS.length]);

function setup(tl) {
  TL = tl;
  TL.scene = SCENES[tl.scene] || SCENES.salon;
  // posiciones de reparto (permite sobrescribir desde el guion)
  TL.pos = Object.assign({}, TL.scene.pos, tl.positions || {});
}

function beatIndexAt(t) {
  const b = TL.beats;
  for (let i = b.length - 1; i >= 0; i--) if (t >= b[i].start) return i;
  return 0;
}

// ---------- cámara ----------
function camFor(beat) {
  const c = beat.cam || "wide";
  if (c === "wide") return { cx: 540, cy: 960, z: 1 };
  const p = TL.pos[c] || TL.pos.yo;
  const z = beat.zoom || 1.45;
  let cx = p.x, cy = p.y + 40 / z;
  cx = clamp(cx, 540 / z, 1080 - 540 / z);
  cy = clamp(cy, 960 / z, 1920 - 960 / z);
  return { cx, cy, z };
}
function camAt(t, i) {
  const b = TL.beats[i];
  const cur = camFor(b);
  const prev = i > 0 ? camFor(TL.beats[i - 1]) : cur;
  const k = easeInOut((t - b.start) / 0.42);
  let c = { cx: lerp(prev.cx, cur.cx, k), cy: lerp(prev.cy, cur.cy, k), z: lerp(prev.z, cur.z, k) };
  // empuje lento (Ken Burns) dentro del beat
  const p = clamp((t - b.start) / Math.max(0.5, b.end - b.start));
  c.z *= 1 + 0.035 * p;
  // temblor
  let sx = 0, sy = 0;
  if (b.shake) {
    const d = t - b.start, a = Math.max(0, 1 - d / 0.6) * 18;
    sx = Math.sin(d * 70) * a; sy = Math.cos(d * 53) * a;
  }
  return { ...c, sx, sy };
}
function worldToScreen(cam, x, y) {
  return { x: 540 + (x - cam.cx) * cam.z + cam.sx, y: 960 + (y - cam.cy) * cam.z + cam.sy };
}

// ---------- personajes ----------
function charState(who, t, i) {
  const b = TL.beats[i];
  const mood = (b.mood && b.mood[who]) || "neutral";
  const prevMood = i > 0 ? (TL.beats[i - 1].mood || {})[who] || "neutral" : mood;
  const frame = Math.min(TL.mouth.length - 1, Math.max(0, Math.round(t * TL.fps)));
  const talking = b.talk === who;
  const mouth = talking ? TL.mouth[frame] : 0;
  // parpadeo
  const period = who === "yo" ? 3.3 : 4.1, off = who === "yo" ? 0.7 : 2.1;
  const ph = ((t + off) % period) / 0.16;
  const blink = ph < 1 ? 1 - Math.abs(ph * 2 - 1) : 0;
  const angry = { angry: 0.45, furious: 0.95 }[mood] || 0;
  const angryPrev = { angry: 0.45, furious: 0.95 }[prevMood] || 0;
  const tint = lerp(angryPrev, angry, easeOutCubic((t - b.start) / 0.5));
  const armT = (b.arm && b.arm[who]) || 0;
  const armP = i > 0 ? ((TL.beats[i - 1].arm || {})[who] || 0) : 0;
  const arm = lerp(armP, armT, easeOutBack((t - b.start) / 0.35));
  const react = mood !== prevMood ? clamp(1 - (t - b.start) / 0.3) : 0;
  return { mood, mouth, blink, tint, arm, t, react, talking };
}

function drawChar(who, t, i) {
  const cfg = TL.cast[who];
  if (!cfg) return "";
  const p = TL.pos[who];
  const st = charState(who, t, i);
  const bob = Math.sin(t * 2.2 + (who === "yo" ? 0 : 1.7)) * 5;
  const sway = st.talking ? Math.sin(t * 7) * 1.6 * (0.4 + st.mouth) : Math.sin(t * 1.3 + 1) * 0.8;
  const squash = 1 + Math.sin(st.react * Math.PI) * 0.06;
  return `<g transform="translate(${p.x} ${p.y + bob}) scale(${p.s * (2 - squash)} ${p.s * squash}) rotate(${sway})">${character(cfg, st)}</g>`;
}

// ---------- efectos ----------
function fxLayer(t, i) {
  const b = TL.beats[i];
  let s = "";
  for (const fx of b.fx || []) {
    const who = fx.on || "yo";
    const p = TL.pos[who];
    const d = t - b.start;
    const S = p.s;
    const hx = p.x, hy = p.y;
    if (fx.type === "stink") {
      for (let k = 0; k < 9; k++) {
        const ph = ((d * 0.7 + k / 9) % 1);
        const dir = fx.dir || 1;
        const x = hx + dir * (60 + ph * 420) * S + Math.sin(ph * 9 + k) * 30;
        const y = hy + 60 * S - ph * 160 + Math.cos(k * 2) * 40;
        const r = (24 + ph * 70) * S;
        s += `<circle cx="${x}" cy="${y}" r="${r}" fill="#8bd346" opacity="${0.55 * (1 - ph) * clamp(d * 3)}" stroke="#5a9c22" stroke-width="4"/>`;
      }
      s += `<g opacity="${clamp(d * 3)}">${[0, 1, 2].map((k) => { const y = hy - 40 + k * 40; const x = hx + 180 * S + Math.sin(d * 6 + k) * 10; return `<path d="M ${x} ${y} q 20 -15 40 0 t 40 0 t 40 0" fill="none" stroke="#5a9c22" stroke-width="8" stroke-linecap="round"/>`; }).join("")}</g>`;
    } else if (fx.type === "steam") {
      for (const side of [-1, 1]) for (let k = 0; k < 3; k++) {
        const ph = (d * 1.4 + k / 3) % 1;
        const x = hx + side * (120 + ph * 90) * S, y = hy - (120 + ph * 160) * S;
        s += `<circle cx="${x}" cy="${y}" r="${(20 + ph * 40) * S}" fill="#fff" opacity="${0.9 * (1 - ph)}" stroke="#c9cfd8" stroke-width="4"/>`;
      }
      s += `<g transform="translate(${hx + 110 * S} ${hy - 150 * S}) scale(${S * (1 + 0.1 * Math.sin(d * 14))})"><path d="M -30 -10 L -6 -10 L -6 -34 M 6 -34 L 6 -10 L 30 -10 M 30 10 L 6 10 L 6 34 M -6 34 L -6 10 L -30 10" fill="none" stroke="#e63946" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/></g>`;
    } else if (fx.type === "sweat") {
      const ph = (d * 0.9) % 1;
      s += `<path transform="translate(${hx + 110 * S} ${hy - 70 * S + ph * 60}) scale(${S})" d="M 0 -26 Q 18 2 14 12 Q 8 26 0 26 Q -8 26 -14 12 Q -18 2 0 -26 Z" fill="#74c0fc" stroke="${INK}" stroke-width="5" opacity="${1 - ph * 0.6}"/>`;
    } else if (fx.type === "pain" || fx.type === "bite") {
      const k = easeOutBack(d / 0.3);
      const x = fx.x ?? hx - 150 * S, y = fx.y ?? hy + 230 * S;
      let pts = [];
      for (let j = 0; j < 16; j++) { const a = (j / 16) * Math.PI * 2; const r = j % 2 ? 50 : 110; pts.push(`${Math.cos(a) * r},${Math.sin(a) * r}`); }
      s += `<g transform="translate(${x} ${y}) scale(${k * (1 + 0.05 * Math.sin(d * 20))}) rotate(${d * 40})"><polygon points="${pts.join(" ")}" fill="#ffd43b" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/></g>`;
      s += `<text x="${x}" y="${y + 18}" font-family="Fredoka" font-size="${54 * k}" text-anchor="middle" fill="#e63946" stroke="${INK}" stroke-width="3">${esc(fx.text || "¡AY!")}</text>`;
    } else if (fx.type === "exclaim" || fx.type === "question") {
      const k = easeOutBack(d / 0.3);
      const ch = fx.type === "exclaim" ? "!" : "?";
      s += `<text x="${hx + 150 * S}" y="${hy - 170 * S}" font-family="Fredoka" font-size="${150 * k * S}" text-anchor="middle" fill="${fx.type === "exclaim" ? "#e63946" : "#3a86ff"}" stroke="${INK}" stroke-width="7" paint-order="stroke" transform="rotate(${12 + Math.sin(d * 8) * 5} ${hx + 150 * S} ${hy - 170 * S})">${ch}</text>`;
    } else if (fx.type === "sparkle") {
      for (let k = 0; k < 7; k++) {
        const a = k * 0.9 + d * 0.8, r = 230 + 30 * Math.sin(k * 3 + d * 3);
        const x = hx + Math.cos(a) * r * S, y = hy - 20 + Math.sin(a) * r * 0.7 * S;
        const sc = 0.5 + 0.5 * Math.abs(Math.sin(d * 4 + k));
        s += `<path transform="translate(${x} ${y}) scale(${sc * S})" d="M 0 -30 Q 4 -4 30 0 Q 4 4 0 30 Q -4 4 -30 0 Q -4 -4 0 -30 Z" fill="#ffd43b" stroke="${INK}" stroke-width="4"/>`;
      }
    } else if (fx.type === "hearts") {
      for (let k = 0; k < 5; k++) {
        const ph = (d * 0.6 + k / 5) % 1;
        s += `<text x="${hx + (k - 2) * 70 * S}" y="${hy - 160 * S - ph * 220}" font-size="${60 * S}" class="emoji" opacity="${1 - ph}" text-anchor="middle">❤️</text>`;
      }
    } else if (fx.type === "zzz") {
      for (let k = 0; k < 3; k++) {
        const ph = (d * 0.5 + k / 3) % 1;
        s += `<text x="${hx + (120 + ph * 80) * S}" y="${hy - (100 + ph * 200) * S}" font-family="Fredoka" font-size="${(40 + ph * 40) * S}" fill="#3a86ff" stroke="${INK}" stroke-width="3" opacity="${1 - ph}">Z</text>`;
      }
    } else if (fx.type === "prop") {
      // objeto emoji pegado al personaje (boca o mano)
      const at = fx.at || "mouth";
      const ox = at === "mouth" ? 40 : at === "hand" ? 190 : 0;
      const oy = at === "mouth" ? 70 : at === "hand" ? 400 : -230;
      const k = easeOutBack(d / 0.35);
      s += `<text x="${hx + ox * S}" y="${hy + oy * S}" font-size="${(fx.size || 120) * S * k}" text-anchor="middle" dominant-baseline="middle" style="font-family:'Noto Color Emoji'" transform="rotate(${fx.rot || -15} ${hx + ox * S} ${hy + oy * S})">${fx.emoji}</text>`;
    } else if (fx.type === "confetti") {
      for (let k = 0; k < 60; k++) {
        const x = (k * 137.5) % 1080, sp = 300 + (k * 53) % 300;
        const y = ((d * sp + k * 97) % 2100) - 100;
        const col = TIP_COLORS[k % TIP_COLORS.length];
        s += `<rect x="${x + Math.sin(d * 3 + k) * 30}" y="${y}" width="22" height="34" fill="${col}" transform="rotate(${d * 200 + k * 30} ${x} ${y})" stroke="${INK}" stroke-width="3"/>`;
      }
    }
  }
  return s;
}

// ---------- interfaz ----------
function currentTip(i) {
  for (let j = i; j >= 0; j--) if (TL.beats[j].tip !== undefined) return { tip: TL.beats[j].tip, since: TL.beats[j].start, j };
  return { tip: null };
}

function tipUI(t, i) {
  const { tip, since } = currentTip(i);
  if (!tip) return "";
  const k = easeOutBack((t - since) / 0.45);
  const y = lerp(-260, 0, k);
  const col = tipColor(tip);
  const kick = tip.kind === "extra" ? "EXTRA" : (tip.kick || "CONSEJO");
  const num = tip.kind === "extra" ? "+" : tip.n;
  const pulse = 1 + 0.12 * Math.sin(clamp((t - since) / 0.6) * Math.PI);
  return `<div class="abs box tip" style="transform: translateY(${y}px)">
    <div class="num" style="background:${col}; transform: scale(${pulse})">${num}</div>
    <div><div class="kick" style="color:${col}">${esc(kick)}</div><div class="lab">${esc(tip.label)}</div></div></div>`;
}

function meterUI(t, i) {
  if (!TL.meter) return "";
  const b = TL.beats[i];
  if (b.meter === undefined || b.meter === null) return "";
  let prev = b.meter;
  for (let j = i - 1; j >= 0; j--) if (TL.beats[j].meter !== undefined && TL.beats[j].meter !== null) { prev = TL.beats[j].meter; break; }
  const firstShow = i === 0 || TL.beats[i - 1].meter === undefined || TL.beats[i - 1].meter === null;
  const v = lerp(prev, b.meter, easeOutCubic((t - b.start - 0.25) / 0.8));
  const col = v > 0.6 ? "#2ecc71" : v > 0.3 ? "#f4a100" : "#e63946";
  const shake = prev > b.meter && t - b.start < 1 ? Math.sin((t - b.start) * 60) * 4 * (1 - (t - b.start)) : 0;
  const app = firstShow ? easeOutBack((t - b.start) / 0.4) : 1;
  return `<div class="abs box meter" style="transform: translateX(${shake}px) scale(${app})">
    <div class="ml">${esc(TL.meter.label)}<small>${esc(TL.meter.sub || "")}</small></div>
    <div class="bar"><div class="fill" style="width:${Math.max(3, v * 100)}%; background:${col}"></div></div></div>`;
}

function cardHTML(c, t, d) {
  const col = c.color || "#e76f51";
  switch (c.type) {
    case "stat": {
      let val = c.value;
      const m = String(c.value).match(/^([^\d]*)(\d+)(.*)$/);
      if (m && c.count !== false) val = m[1] + Math.round(lerp(0, +m[2], easeOutCubic((d - 0.15) / 0.9))) + m[3];
      return `<div style="display:flex;align-items:center;gap:36px;justify-content:center">
        ${c.emoji ? `<div class="emoji" style="font-size:170px; transform: rotate(${Math.sin(d * 5) * 6}deg)">${c.emoji}</div>` : ""}
        <div><div class="k" style="color:${col}">${esc(c.label)}</div><div class="big" style="color:${c.valueColor || "#e63946"}">${esc(val)}</div>
        ${c.sub ? `<div class="sm">${esc(c.sub)}</div>` : ""}</div></div>`;
    }
    case "timer": {
      const blink = Math.floor(d * 2) % 2 ? 0.25 : 1;
      const parts = String(c.value).split(":");
      const v = parts.length === 2 ? `${parts[0]}<span style="opacity:${blink}">:</span>${parts[1]}` : esc(c.value);
      return `<div class="k" style="color:${col}">${esc(c.label)}</div><div class="big" style="font-variant-numeric: tabular-nums">${v}</div>${c.sub ? `<div class="sm">${esc(c.sub)}</div>` : ""}`;
    }
    case "receipt": {
      const rows = (c.rows || []).map((r, j) => {
        const app = r.new ? easeOutBack((d - 0.2 - j * 0.12) / 0.35) : 1;
        return `<div class="row ${r.hl ? "hl" : ""}" style="transform: scale(${app}); opacity:${clamp(app)}"><span>${esc(r.l)}</span><span>${esc(r.v)}</span></div>`;
      }).join("");
      return `<div class="mid">${esc(c.title || "FACTURA")}</div><div class="sm">${esc(c.sub || "")}</div><div class="dash"></div>
        <div style="text-align:left">${rows}</div><div class="dash"></div>
        <div class="row" style="font-size:42px"><span>TOTAL</span><span>${esc(c.total)}</span></div>`;
    }
    case "check": {
      const k = easeOutBack((d - 0.35) / 0.35);
      return `<div style="display:flex;align-items:center;gap:36px;justify-content:center">
        ${c.emoji ? `<div class="emoji" style="font-size:150px">${c.emoji}</div>` : ""}
        <div style="text-align:left"><div class="k" style="color:${col}">${esc(c.label)}</div><div class="mid">${esc(c.value)}</div></div></div>
        <div class="stamp" style="background:${c.ok === false ? "#e63946" : "#2ecc71"}; transform: scale(${k}) rotate(${lerp(-40, 10, clamp(k))}deg)">${c.ok === false ? "✕" : "✓"}</div>`;
    }
    case "versus": {
      return `<div class="k" style="color:${col}">${esc(c.label || "")}</div>
        <div style="display:flex;align-items:center;justify-content:space-around;margin-top:10px">
          <div><div class="emoji" style="font-size:130px">${c.a.emoji}</div><div class="sm">${esc(c.a.label)}</div></div>
          <div class="big" style="font-size:80px;color:#e63946">VS</div>
          <div><div class="emoji" style="font-size:130px">${c.b.emoji}</div><div class="sm">${esc(c.b.label)}</div></div></div>`;
    }
    case "list": {
      return `<div class="k" style="color:${col}">${esc(c.label || "")}</div>` + (c.items || []).map((it, j) => {
        const app = easeOutBack((d - 0.15 - j * 0.25) / 0.35);
        return `<div class="row" style="transform: scale(${app}); opacity:${clamp(app)}; font-size:38px"><span>${it.emoji ? `<span class="emoji">${it.emoji}</span> ` : ""}${esc(it.l)}</span><span>${esc(it.v || "")}</span></div>`;
      }).join("");
    }
    default: // note
      return `<div style="display:flex;align-items:center;gap:36px;justify-content:center">
        ${c.emoji ? `<div class="emoji" style="font-size:160px; transform: rotate(${Math.sin(d * 4) * 8}deg)">${c.emoji}</div>` : ""}
        <div style="text-align:left"><div class="k" style="color:${col}">${esc(c.label || "")}</div><div class="mid">${esc(c.value || "")}</div>${c.sub ? `<div class="sm">${esc(c.sub)}</div>` : ""}</div></div>`;
  }
}

function cardUI(t, i) {
  const b = TL.beats[i];
  const c = b.card;
  if (!c) return "";
  if (c.type === "title") return hookUI(t, i);
  if (c.type === "summary") return "";
  // inicio de la tarjeta (si continúa desde beats anteriores con el mismo id)
  let start = b.start;
  for (let j = i - 1; j >= 0; j--) { const pc = TL.beats[j].card; if (c.id && pc && pc.id === c.id) start = TL.beats[j].start; else break; }
  const next = TL.beats[i + 1];
  const continues = next && next.card && c.id && next.card.id === c.id;
  const d = t - start;
  let k = easeOutBack(d / 0.4);
  let op = 1;
  if (!continues) { const out = clamp((t - (b.end - 0.18)) / 0.18); k *= 1 - 0.3 * out; op = 1 - out; }
  const rot = (c.tilt ?? -2) * (1 - clamp(d / 0.5)) + Math.sin(d * 1.5) * 0.6;
  const top = c.top || (TL.beats.some((x) => x.tip) ? 360 : 200);
  return `<div class="abs box card" style="top:${top}px; transform: translateX(-50%) scale(${k}) rotate(${rot}deg); opacity:${op}">${cardHTML(c, t, d)}</div>`;
}

function hookUI(t, i) {
  const b = TL.beats[i];
  const c = b.card;
  let start = b.start;
  for (let j = i - 1; j >= 0; j--) { const pc = TL.beats[j].card; if (pc && pc.type === "title") start = TL.beats[j].start; else break; }
  const d = t - start;
  const next = TL.beats[i + 1];
  const continues = next && next.card && next.card.type === "title";
  let k = easeOutBack(d / 0.45);
  let op = 1;
  if (!continues) { const out = clamp((t - (b.end - 0.2)) / 0.2); k *= 1 - 0.4 * out; op = 1 - out; }
  const tagK = easeOutBack((d - 0.5) / 0.35);
  return `<div class="abs box hook" style="transform: translateX(-50%) scale(${k}) rotate(${Math.sin(d * 2) * 1}deg); opacity:${op}">
    ${c.emoji ? `<div class="emoji" style="font-size:110px; margin-bottom:6px">${c.emoji}</div>` : ""}
    <div class="t" style="color:${c.color || "#2a9d8f"}">${esc(c.title)}</div>
    ${c.sub ? `<div class="s">${esc(c.sub)}</div>` : ""}
    ${c.tag ? `<div class="tag" style="transform: rotate(-3deg) scale(${tagK})">${esc(c.tag)}</div>` : ""}</div>`;
}

function bubbleUI(t, i, cam) {
  const b = TL.beats[i];
  if (!b.quote) return "";
  const who = b.quote.who || b.talk || "yo";
  const p = TL.pos[who];
  const head = worldToScreen(cam, p.x, p.y - 190 * p.s);
  const d = t - b.start;
  const k = easeOutBack((d - 0.05) / 0.35);
  const left = head.x < 540;
  const x = clamp(left ? head.x - 120 : head.x - 520, 30, 1080 - 30 - 640);
  const y = Math.max(330, head.y - 240);
  return `<div class="abs box bubble ${left ? "l" : "r"}" style="left:${x}px; top:${y}px; transform: scale(${k}) rotate(${left ? -2 : 2}deg)">${esc(b.quote.text)}</div>`;
}

function subsUI(t, i) {
  const b = TL.beats[i];
  if (!b.chunks || b.hideSubs) return "";
  let ch = null;
  for (const c of b.chunks) if (t >= c.s - 0.05) ch = c;
  if (!ch || t > b.end) return "";
  const words = ch.words.map((w) => {
    const on = t >= w.s && t < w.e + 0.08;
    const pop = on ? 1 + 0.14 * Math.sin(clamp((t - w.s) / 0.18) * Math.PI) : 1;
    const appear = easeOutBack((t - ch.s + 0.05) / 0.16);
    return `<span class="w ${on ? "on" : ""} ${w.em ? "em" : ""}" style="transform: scale(${pop * appear}) rotate(${on ? -2 : 0}deg)">${esc(w.w)}</span>`;
  }).join("");
  return `<div class="abs subs">${words}</div>`;
}

function summaryUI(t, i) {
  const b = TL.beats[i];
  if (!b.card || b.card.type !== "summary") return "";
  const c = b.card;
  const d = t - b.start;
  const items = TL.tips.map((tip, j) => {
    const k = easeOutBack((d - 0.2 - j * 0.22) / 0.35);
    const xk = easeOutBack((d - 0.5 - j * 0.22) / 0.3);
    return `<div class="box sitem" style="transform: translateX(${lerp(-900, 0, clamp(k))}px) scale(${Math.max(0, k)})">
      <div class="n" style="background:${tipColor(tip)}">${tip.kind === "extra" ? "+" : tip.n}</div>
      <div class="lab">${esc(tip.short || tip.label)}</div>
      ${c.marks === false ? "" : `<div class="x" style="transform: scale(${xk})">✕</div>`}</div>`;
  }).join("");
  const ctaK = easeOutBack((d - 0.4 - TL.tips.length * 0.22) / 0.4);
  const pulse = 1 + 0.05 * Math.sin(d * 7);
  return `<div class="abs summary">
    <h1 style="transform: scale(${easeOutBack(d / 0.4)})">${esc(c.title || "RESUMEN")}</h1>
    <div class="sub">${esc(c.sub || "")}</div>${items}
    <div class="cta" style="transform: scale(${ctaK * pulse})">${esc(c.cta || "SÍGUEME")}</div>
    <div class="cta-sub" style="opacity:${clamp(ctaK)}">${esc(c.ctaSub || "")}</div></div>`;
}

// ---------- fotograma ----------
function renderAt(t) {
  const i = beatIndexAt(t);
  const b = TL.beats[i];
  const cam = camAt(t, i);
  const sc = TL.scene;
  const tr = `translate(${540 + cam.sx} ${960 + cam.sy}) scale(${cam.z}) translate(${-cam.cx} ${-cam.cy})`;
  const isSummary = b.card && b.card.type === "summary";
  const dim = isSummary ? clamp((t - b.start) / 0.4) * 0.72 : 0;
  // orden de dibujo: el que no está en foco detrás
  const order = b.front === "otro" ? ["yo", "otro"] : ["otro", "yo"];
  document.getElementById("stage").innerHTML = `
    <g transform="${tr}">
      ${sc.bg(t)}
      ${order.map((w) => drawChar(w, t, i)).join("")}
      ${sc.fg(t)}
      ${fxLayer(t, i)}
    </g>
    <rect width="1080" height="1920" fill="#14161f" opacity="${dim}"/>
    <radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".22"/></radialGradient>
    <rect width="1080" height="1920" fill="url(#vig)"/>`;
  document.getElementById("ui").innerHTML =
    (isSummary ? summaryUI(t, i) : tipUI(t, i) + meterUI(t, i) + cardUI(t, i) + bubbleUI(t, i, cam)) +
    subsUI(t, i) +
    (TL.handle ? `<div class="abs handle">${esc(TL.handle)}</div>` : "");
}

window.setup = setup;
window.renderAt = renderAt;
