// Capture real, crisp screenshots of https://pikment.az for use in videos.
// Usage: NODE_PATH=$(npm root -g) node pikment-studio/tools/capture_site.js [outDir]
// Output: <outDir>/{desktop,mobile}_<section>.png (+ full hero views). Default outDir is
// remotion-composer/public/pikment_site (gitignored; regenerate any time).
const { chromium } = require('playwright');
const path = require('path');
const out = process.argv[2] || path.join(__dirname, '../../remotion-composer/public/pikment_site');
const SECTIONS = ['esas', 'reqemler', 'kimler', 'xidmetler', 'mentorluq', 'telimler', 'telimciler', 'tetbiq', 'suallar', 'muraciet'];
(async () => {
  const b = await chromium.launch();
  for (const [name, vp, dpr] of [['desktop', { width: 1440, height: 900 }, 2], ['mobile', { width: 390, height: 844 }, 3]]) {
    const p = await b.newPage({ viewport: vp, deviceScaleFactor: dpr });
    await p.goto('https://pikment.az/', { waitUntil: 'networkidle', timeout: 60000 });
    await p.waitForTimeout(1500);
    await p.screenshot({ path: path.join(out, `${name}_hero.png`) });
    for (const id of SECTIONS) {
      const el = p.locator(`#${id}`).first();
      if (!(await el.count())) { console.log('skip', name, id); continue; }
      await el.scrollIntoViewIfNeeded();
      await p.waitForTimeout(700);
      await el.screenshot({ path: path.join(out, `${name}_${id}.png`) });
      console.log('ok', name, id);
    }
    await p.close();
  }
  await b.close();
})();
