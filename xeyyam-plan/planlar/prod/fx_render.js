// İstifadə: node neuron_render.js <html> <outdir> '<windows json>'  — window: {a,b,l0,l1,burst}
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [html, out, wj] = process.argv.slice(2); const W = JSON.parse(wj); const FPS = 30;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.resolve(html));
  for (let k = 0; k < W.length; k++) {
    const w = W[k]; const dir = path.join(out, 'w' + k); fs.mkdirSync(dir, { recursive: true });
    const n = Math.round((w.b - w.a) * FPS);
    for (let i = 0; i < n; i++) {
      const t = w.a + i / FPS, u = i / (n - 1);
      const alpha = Math.min(1, (t - w.a) / 0.45, (w.b - t) / (w.hold ? 1e9 : 0.45));
      await p.evaluate(([th, t, l, a, bu, op]) => draw(th, t, l, a, bu, op), [w.theme, t, w.l0 + (w.l1 - w.l0) * u, Math.max(0, alpha), w.burst ? u : 0, w.opts || {}]);
      await p.locator('#c').screenshot({ path: path.join(dir, String(i).padStart(4, '0') + '.png'), omitBackground: true });
    }
    console.log('w' + k, n);
  }
  await b.close();
})();
