// Video kadrları: node vshoot.js <file.html> <framesDir> [hash] [fps=30]
// HTML window.TIMES.TOTAL (san) və window.renderFrame(t) təyin etməlidir; document.title='done'.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path'), fs = require('fs');
const [html, out, hash = '', fpsArg] = process.argv.slice(2); const fps = +(fpsArg || 30);
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.error('pageerror:', e.message));
  await p.goto('file://' + path.resolve(html) + (hash ? '#' + hash : ''));
  await p.waitForFunction(() => document.title === 'done', null, { timeout: 30000 });
  const [w, h, T] = await p.evaluate(() => [parseInt(getComputedStyle(document.body).width), parseInt(getComputedStyle(document.body).height), window.TIMES.TOTAL]);
  const n = Math.round(T * fps);
  for (let i = 0; i < n; i++) { await p.evaluate(t => renderFrame(t), i / fps); await p.screenshot({ path: path.join(out, String(i).padStart(5, '0') + '.png'), clip: { x: 0, y: 0, width: w, height: h } }); }
  console.log(JSON.stringify({ frames: n, w, h, T, fps })); await b.close();
})();
