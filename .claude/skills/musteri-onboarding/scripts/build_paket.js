// Strateji paket PDF: node build_paket.js <paket.json> <out.pdf>
// Agentlik rəngləri sabitdir (Aynur Məmmədova); müştəri palitrası yalnız "Vizual istiqamət" bölməsində göstərilir.
const { chromium } = require('/opt/node22/lib/node_modules/playwright'); const fs = require('fs'), path = require('path');
const [src, out] = process.argv.slice(2); if (!src || !out) { console.error('usage: node build_paket.js paket.json out.pdf'); process.exit(1); }
const P = JSON.parse(fs.readFileSync(src, 'utf8'));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); p.on('pageerror', e => console.error('pageerror:', e.message));
  await p.addInitScript(d => { window.P = d }, P);
  await p.goto('file://' + path.join(__dirname, '..', 'assets', 'paket.html'));
  await p.waitForFunction(() => document.title === 'done', null, { timeout: 30000 }); await p.waitForTimeout(300);
  await p.pdf({ path: out, format: 'A4', printBackground: true }); await b.close(); console.log(out);
})();
