#!/usr/bin/env node
// Render an Instagram carousel (1080x1350 PNG per slide) from a slides JSON
// file and a client brand JSON file. No generative AI is involved, so the
// output carries no AI-content metadata, and text is typeset, not drawn.
//
//   node render.js slides.json brand.json out_dir/
//
// slides.json: { "slides": [ {type, ...}, ... ] }
//   cover     { label, headline, highlight?, sub?, photo? }  photo: local image path
//   statement { text }
//   point     { n, headline, body }
//   recap     { headline, items: [..] }
//   cta       { headline, body? }
// brand.json: { colors: {navy, blue, cream, gold}, name_line, handle }

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const [slidesPath, brandPath, outDir] = process.argv.slice(2);
if (!slidesPath || !brandPath || !outDir) {
  console.error('usage: node render.js slides.json brand.json out_dir/');
  process.exit(2);
}

const spec = JSON.parse(fs.readFileSync(slidesPath, 'utf8'));
const brand = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
const c = brand.colors;
const fontDir = path.join(__dirname, 'fonts');

const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function headlineHtml(text, highlight) {
  const t = esc(text);
  if (!highlight || !text.includes(highlight)) return t;
  return t.replace(esc(highlight), `<span class="hl">${esc(highlight)}</span>`);
}

function frame(inner, i, total, dark = false) {
  return `<section class="slide${dark ? ' dark' : ''}">
    <div class="circle"></div>
    <div class="num">${i}/${total}</div>
    ${inner}
    <div class="foot"><span>${esc(brand.name_line)}</span><span>${esc(brand.handle)}</span></div>
  </section>`;
}

function slideHtml(s, i, total) {
  switch (s.type) {
    case 'cover':
      return frame(`
        <div class="label"><span>${esc(s.label)}</span><i></i></div>
        <h1 class="cover-h">${headlineHtml(s.headline, s.highlight)}</h1>
        <div class="gold"></div>
        ${s.sub ? `<p class="sub"${s.photo ? ' style="max-width:400px"' : ''}>${esc(s.sub)}</p>` : ''}
        ${s.photo ? `<img class="photo" src="file://${path.resolve(path.dirname(slidesPath), s.photo)}">` : ''}`, i, total);
    case 'statement':
      return frame(`<p class="statement">${esc(s.text)}</p><div class="gold"></div>`, i, total);
    case 'point':
      return frame(`
        <div class="pn">${esc(s.n)}</div>
        <h2 class="point-h">${esc(s.headline)}</h2>
        <div class="gold"></div>
        <p class="body">${esc(s.body)}</p>`, i, total);
    case 'recap':
      return frame(`
        <h2 class="point-h">${esc(s.headline)}</h2>
        <div class="gold"></div>
        <ol class="recap">${s.items.map((it, k) =>
          `<li><b>${String(k + 1).padStart(2, '0')}</b><span>${esc(it)}</span></li>`).join('')}</ol>`,
        i, total);
    case 'cta':
      return frame(`
        <h2 class="cta-h">${esc(s.headline)}</h2>
        <div class="gold"></div>
        ${s.body ? `<p class="body">${esc(s.body)}</p>` : ''}`, i, total, true);
    default:
      throw new Error(`unknown slide type: ${s.type}`);
  }
}

const css = `
@font-face{font-family:M;src:url("file://${fontDir}/Montserrat-400.ttf");font-weight:400}
@font-face{font-family:M;src:url("file://${fontDir}/Montserrat-500.ttf");font-weight:500}
@font-face{font-family:M;src:url("file://${fontDir}/Montserrat-700.ttf");font-weight:700}
@font-face{font-family:M;src:url("file://${fontDir}/Montserrat-800.ttf");font-weight:800}
*{margin:0;padding:0;box-sizing:border-box}
body{background:#ccc}
.slide{position:relative;width:1080px;height:1350px;overflow:hidden;
  background:${c.cream};color:${c.navy};font-family:M,sans-serif;
  padding:150px 120px 0 120px}
.slide.dark{background:${c.navy};color:${c.cream}}
.circle{position:absolute;width:900px;height:900px;border-radius:50%;
  right:-420px;bottom:-380px;background:${c.blue};opacity:.55}
.dark .circle{opacity:.12}
.num{position:absolute;top:70px;right:120px;font-size:30px;font-weight:500;opacity:.6}
.label{display:flex;align-items:center;gap:22px;margin-bottom:56px;
  font-size:26px;font-weight:700;letter-spacing:.32em}
.label i{display:block;flex:1;height:2px;background:currentColor;position:relative}
.label i::after{content:"";position:absolute;right:-6px;top:-5px;width:12px;height:12px;
  border-radius:50%;background:currentColor}
.photo{position:absolute;right:120px;bottom:150px;width:400px;height:520px;
  object-fit:cover;border-radius:200px 200px 24px 24px}
.cover-h{margin-top:90px;font-size:118px;line-height:1.04;font-weight:800;letter-spacing:-.01em}
.hl{background:${c.blue};padding:0 .14em;border-radius:12px;white-space:nowrap}
.gold{width:140px;height:7px;background:${c.gold};border-radius:4px;margin:52px 0 44px}
.sub{font-size:40px;font-weight:500;line-height:1.35;max-width:780px}
.statement{font-size:66px;font-weight:700;line-height:1.22;margin-top:120px;max-width:840px}
.pn{font-size:150px;font-weight:800;color:${c.gold};line-height:1;margin-bottom:36px}
.point-h{font-size:76px;font-weight:800;line-height:1.08;max-width:840px}
.body{font-size:42px;font-weight:400;line-height:1.48;max-width:820px}
.recap{list-style:none;margin-top:10px}
.recap li{display:flex;gap:34px;align-items:baseline;font-size:46px;font-weight:600;
  padding:26px 0;border-bottom:2px solid ${c.blue}}
.recap b{font-weight:800;color:${c.gold};font-size:40px;min-width:62px}
.cta-h{font-size:104px;font-weight:800;line-height:1.05;margin-top:200px;max-width:860px}
.foot{position:absolute;left:120px;right:120px;bottom:70px;display:flex;
  justify-content:space-between;font-size:26px;font-weight:500;opacity:.75;white-space:nowrap}
`;

(async () => {
  const total = spec.slides.length;
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head>
    <body>${spec.slides.map((s, k) => slideHtml(s, k + 1, total)).join('')}</body></html>`;
  fs.mkdirSync(outDir, { recursive: true });
  const htmlPath = path.join(outDir, 'carousel.html');
  fs.writeFileSync(htmlPath, html);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  await page.goto('file://' + path.resolve(htmlPath));
  await page.evaluate(() => document.fonts.ready);
  const slides = await page.$$('section.slide');
  for (let k = 0; k < slides.length; k++) {
    const out = path.join(outDir, `${String(k + 1).padStart(2, '0')}.png`);
    await slides[k].screenshot({ path: out });
    console.log(out);
  }
  // Fail loudly if any text overflows the slide instead of shipping a cut-off.
  const overflow = await page.$$eval('section.slide', (els) => els
    .map((el, k) => [...el.querySelectorAll('h1,h2,p,ol')]
      .some((n) => n.getBoundingClientRect().bottom > el.getBoundingClientRect().bottom - 120)
      ? k + 1 : 0)
    .filter(Boolean));
  await browser.close();
  if (overflow.length) {
    console.error(`text runs into the footer on slide(s): ${overflow.join(', ')}`);
    process.exit(1);
  }
})();
