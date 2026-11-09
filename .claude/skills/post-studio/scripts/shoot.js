// Statik render: node shoot.js <file.html> <outDir> [hash1 hash2 ...]
// HTML document.title='done' qoyanda çəkir. Ölçü: body inline width/height, yoxsa 1080x1350.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path'), fs = require('fs');
const [html, out, ...ids] = process.argv.slice(2);
if (!html || !out) { console.error('usage: node shoot.js <file.html> <outDir> [hash...]'); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.error('pageerror:', e.message));
  for (const id of (ids.length ? ids : [''])) {
    await p.goto('file://' + path.resolve(html) + (id ? '#' + id : '')); await p.reload();
    await p.waitForFunction(() => document.title === 'done', null, { timeout: 30000 }).catch(() => console.error('title!=done, render davam edir'));
    await p.waitForTimeout(200);
    const [w, h] = await p.evaluate(() => [parseInt(getComputedStyle(document.body).width) || 1080, parseInt(getComputedStyle(document.body).height) || 1350]);
    await p.setViewportSize({ width: w, height: h }); await p.waitForTimeout(100);
    const f = path.join(out, (id || path.basename(html, '.html')) + '.png');
    await p.screenshot({ path: f, clip: { x: 0, y: 0, width: w, height: h } }); console.log(f, w + 'x' + h);
  }
  await b.close();
})();
