// Capture one tall desktop screenshot of pikment.az from the top down to (not including) the trainers section,
// for smooth "live scroll" shots inside the laptop mockup. Usage: NODE_PATH=$(npm root -g) node pikment-studio/tools/capture_scroll.js
const { chromium } = require('playwright');
const path = require('path');
const out = path.join(__dirname, '../../remotion-composer/public/pikment_launch/site_scroll.png');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
  await p.goto('https://pikment.az/', { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(1500);
  const h = await p.evaluate(() => { document.querySelectorAll('*').forEach(e => { e.style.scrollBehavior = 'auto'; });
    const t = document.querySelector('#telimciler'); return Math.round(t.getBoundingClientRect().top + window.scrollY); });
  // trigger lazy/reveal animations
  for (let y = 0; y < h; y += 400) { await p.evaluate(v => window.scrollTo(0, v), y); await p.waitForTimeout(150); }
  await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(600);
  await p.screenshot({ path: out, fullPage: true, clip: { x: 0, y: 0, width: 1440, height: h } });
  console.log('height css px', h);
  await b.close();
})();
