// Kart kadrları: lib.html səhnələrini kadr-kadr PNG-yə çəkir. Paralel: WORKERS səhifə eyni anda işləyir.
// İstifadə: node render.js jobs.json   (jobs: [{scene, dur, p, dir}])
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
const fs = require('fs'); const path = require('path');
const JOBS = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')); const FPS = 30;
const WORKERS = Math.max(1, parseInt(process.env.PRO_WORKERS || '3', 10));
(async () => {
  const b = await chromium.launch();
  const tasks = [];
  for (const j of JOBS) {
    fs.rmSync(j.dir, { recursive: true, force: true }); fs.mkdirSync(j.dir, { recursive: true });
    const n = Math.round(j.dur * FPS);
    for (let i = 0; i < n; i++) tasks.push([j, i]);
  }
  let next = 0;
  async function worker() {
    const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    await pg.goto('file://' + path.join(__dirname, 'lib.html')); await pg.waitForLoadState('networkidle');
    await pg.evaluate(async () => { for (const w of [600, 700, 800, 900]) await document.fonts.load(w + ' 80px Montserrat'); await document.fonts.load('italic 40px Lora'); await document.fonts.ready; });
    while (next < tasks.length) {
      const [j, i] = tasks[next++];
      await pg.evaluate(([nm, t, D, p]) => renderAt(nm, t, D, p), [j.scene, i / FPS, j.dur, j.p || {}]);
      await pg.screenshot({ path: path.join(j.dir, String(i).padStart(5, '0') + '.png'), omitBackground: true });
    }
    await pg.close();
  }
  await Promise.all(Array.from({ length: WORKERS }, worker));
  for (const j of JOBS) console.log('kadrlar', j.dir, Math.round(j.dur * FPS));
  await b.close();
})();
