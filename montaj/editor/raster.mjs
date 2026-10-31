// Qrafika elementlərini şəffaf PNG-yə çevirir (render üçün) — redaktor önizləməsi ilə EYNİ graphics.js.
// İstifadə: node raster.mjs <jobs.json> <out_dir>
//   jobs.json: { W, H, theme, fonts: [{family, weight, path, range}], jobs: [{name, clip, tl}] }
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const [jobsFile, outDir] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });
const faces = cfg.fonts.map((f) => `@font-face{font-family:"${f.family}";font-weight:${f.weight};src:url("${pathToFileURL(f.path)}") format("woff2");unicode-range:${f.range}}`).join('\n');
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${faces}
html,body{margin:0;background:transparent}#stage{position:relative;width:${cfg.W}px;height:${cfg.H}px}
#el{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:max-content;max-width:100%}</style></head>
<body><div id="stage"><div id="el"></div></div><script>${fs.readFileSync(path.join(here, 'graphics.js'), 'utf8')}</script></body></html>`;
const page_file = path.join(outDir, '_raster.html');
fs.writeFileSync(page_file, html);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: cfg.W, height: cfg.H }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(page_file).href);
await page.evaluate(async (fams) => { await Promise.all(fams.map((f) => document.fonts.load(`${f.weight} 40px "${f.family}"`, 'əğıöüşçƏĞİÖÜŞÇ abc'))); await document.fonts.ready; }, cfg.fonts);
const res = {};
for (const j of cfg.jobs) {
  const box = await page.evaluate(({ clip, tl, H, theme }) => {
    const el = document.getElementById('el');
    el.replaceChildren(window.MG.build(document, clip, H, theme, tl));
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top, w: r.width, h: r.height };
  }, { clip: j.clip, tl: j.tl, H: cfg.H, theme: cfg.theme });
  const m = Math.ceil(cfg.H * 0.012); // yazı konturu üçün ehtiyat
  const clipRect = { x: Math.max(0, box.x - m), y: Math.max(0, box.y - m), width: Math.min(cfg.W, box.w + 2 * m), height: Math.min(cfg.H, box.h + 2 * m) };
  const out = path.join(outDir, `${j.name}.png`);
  await page.screenshot({ path: out, clip: clipRect, omitBackground: true });
  res[j.name] = { file: out, w: Math.round(clipRect.width), h: Math.round(clipRect.height) };
}
await browser.close();
fs.writeFileSync(path.join(outDir, '_result.json'), JSON.stringify(res));
console.log(`raster: ${cfg.jobs.length} element`);
