// Renderiza los fotogramas de un timeline con Chromium (Playwright) en paralelo.
// Uso: node engine/render.js timeline.json carpeta_frames [workers] [solo_frame]
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

(async () => {
  const [tlPath, outDir, workersArg, onlyFrame] = process.argv.slice(2);
  const tl = JSON.parse(fs.readFileSync(tlPath, "utf8"));
  fs.mkdirSync(outDir, { recursive: true });
  const total = Math.ceil(tl.duration * tl.fps);
  const frames = onlyFrame !== undefined ? onlyFrame.split(",").map(Number) : [...Array(total).keys()];
  const workers = Math.max(1, Math.min(+workersArg || 3, frames.length));
  const browser = await chromium.launch();
  const url = "file://" + path.resolve(__dirname, "index.html");
  let done = 0;
  const t0 = Date.now();
  const work = async (w) => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    await page.goto(url);
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate((tl) => window.setup(tl), tl);
    // precarga de fuentes/emoji
    await page.evaluate(() => window.renderAt(0));
    await page.waitForTimeout(300);
    for (let k = w; k < frames.length; k += workers) {
      const f = frames[k];
      await page.evaluate((t) => window.renderAt(t), f / tl.fps);
      await page.screenshot({ path: path.join(outDir, `f${String(f).padStart(5, "0")}.jpg`), type: "jpeg", quality: 95 });
      done++;
      if (done % 100 === 0) process.stdout.write(`  ${done}/${frames.length} fotogramas (${((Date.now() - t0) / 1000).toFixed(0)}s)\n`);
    }
    await page.close();
  };
  await Promise.all([...Array(workers).keys()].map(work));
  await browser.close();
  console.log(`render ok: ${frames.length} fotogramas en ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch((e) => { console.error(e); process.exit(1); });
