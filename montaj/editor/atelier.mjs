// Bəzək rejimi: əl ilə yazılmış HTML səhnəni deterministik kadr-kadr çəkir (PNG ardıcıllığı).
// İstifadə: node atelier.mjs <cfg.json>   cfg: { html, outDir, W, H, fps, dur, fonts: [{family, weight, path, range}], theme }
// HTML müqaviləsi: window.setTime(t) — t saniyəyə görə səhnəni qurur (animasiya YALNIZ t-dən asılıdır, Date/requestAnimationFrame yox).
// window.ATELIER_CTX = {W, H, fps, dur, theme} səhnə yüklənməmişdən əvvəl verilir.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
fs.mkdirSync(cfg.outDir, { recursive: true });
const faces = (cfg.fonts || []).map((f) => `@font-face{font-family:"${f.family}";font-weight:${f.weight};src:url("${pathToFileURL(f.path)}") format("${f.fmt || 'woff2'}");unicode-range:${f.range}}`).join('\n');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: cfg.W, height: cfg.H }, deviceScaleFactor: 1 });
await page.addInitScript((ctx) => { window.ATELIER_CTX = ctx; }, { W: cfg.W, H: cfg.H, fps: cfg.fps, dur: cfg.dur, theme: cfg.theme || {} });
await page.goto(pathToFileURL(path.resolve(cfg.html)).href);
await page.addStyleTag({ content: faces });
await page.evaluate(async () => { await document.fonts.ready; });
const ok = await page.evaluate(() => typeof window.setTime === 'function');
if (!ok) { console.error('HTML-də window.setTime(t) yoxdur'); await browser.close(); process.exit(3); }
const n = Math.max(1, Math.round(cfg.dur * cfg.fps));
for (let i = 0; i < n; i++) {
  await page.evaluate((t) => window.setTime(t), i / cfg.fps);
  await page.screenshot({ path: path.join(cfg.outDir, `f_${String(i).padStart(5, '0')}.png`), type: 'png' });
}
await browser.close();
console.log(n);
