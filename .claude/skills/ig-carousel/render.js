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
//   photo     { photo?, hint?, headline, body? }   photo on top, text below
//   overlay   { photo?, hint?, headline, body? }   full-bleed photo, text on navy fade
//   compare   { label_bad?, bad, label_good?, good, note? }  "say this, not that"
// photo paths are relative to slides.json; with no photo a labelled
// placeholder (hint) is drawn so a layout can be approved before photos exist.
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

function img(s, cls) {
  if (s.photo) {
    return `<img class="${cls}" src="file://${path.resolve(path.dirname(slidesPath), s.photo)}">`;
  }
  return `<div class="${cls} ph-empty"><span>FOTO${s.hint ? ': ' + esc(s.hint) : ''}</span></div>`;
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
    case 'photo':
      return frame(`
        ${img(s, 'ph-top')}
        <div class="ph-text">
          <h2 class="point-h sm">${esc(s.headline)}</h2>
          ${s.body ? `<p class="body sm">${esc(s.body)}</p>` : ''}
        </div>`, i, total);
    case 'overlay':
      return frame(`
        ${img(s, 'ph-full')}
        <div class="ph-fade"></div>
        <div class="ov-text">
          <h2 class="point-h">${esc(s.headline)}</h2>
          <div class="gold"></div>
          ${s.body ? `<p class="body">${esc(s.body)}</p>` : ''}
        </div>`, i, total, true);
    case 'compare':
      return frame(`
        <div class="cmp bad"><div class="cmp-l">${esc(s.label_bad || 'Belə yox')}</div>
          <p>${esc(s.bad)}</p></div>
        <div class="cmp good"><div class="cmp-l">${esc(s.label_good || 'Belə')}</div>
          <p>${esc(s.good)}</p></div>
        ${s.note ? `<p class="body sm">${esc(s.note)}</p>` : ''}`, i, total);
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
.num{position:absolute;z-index:2;top:70px;right:120px;font-size:30px;font-weight:500;opacity:.6}
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
.ph-top{position:absolute;left:0;top:0;width:1080px;height:720px;object-fit:cover}
.ph-full{position:absolute;inset:0;width:1080px;height:1350px;object-fit:cover}
.ph-empty{display:flex;align-items:center;justify-content:center;background:${c.blue};
  color:${c.navy};font-size:32px;font-weight:600;letter-spacing:.04em;text-align:center;padding:60px}
.ph-fade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,30,58,0) 30%,${c.navy} 78%)}
.ph-text{position:absolute;left:120px;right:120px;top:790px}
.ov-text{position:absolute;left:120px;right:120px;bottom:170px}
.ov-text .gold{margin:36px 0 30px}
.point-h.sm{font-size:64px}
.body.sm{font-size:38px;margin-top:26px}
.cmp{border-radius:28px;padding:44px 50px;margin-bottom:34px}
.cmp-l{font-size:26px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;margin-bottom:18px}
.cmp p{font-size:50px;font-weight:700;line-height:1.25}
.cmp.bad{background:rgba(14,30,58,.06);color:rgba(14,30,58,.55)}
.cmp.bad p{text-decoration:line-through;text-decoration-thickness:4px}
.cmp.good{background:${c.navy};color:${c.cream}}
.cmp.good .cmp-l{color:${c.gold}}
.foot{position:absolute;z-index:2;left:120px;right:120px;bottom:70px;display:flex;
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
