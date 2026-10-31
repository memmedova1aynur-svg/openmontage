// Telefon redaktoru (artifact şablonu) — Chromium + iPhone ölçüsü emulyasiyası (real Safari DEYİL):
//   node tests/montaj/e2e_editor.mjs <editor/index.html> <out.json>
import { createRequire } from 'node:module';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');
const [file, outJson] = process.argv.slice(2);
const log = (...a) => console.log('[redaktor]', ...a);

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext({ ...devices['iPhone 13'] });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
await page.goto('file://' + file);
await page.waitForFunction(() => window.__editor && document.querySelector('#vid').readyState >= 1, null, { timeout: 15000 });
assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'üfüqi daşma yoxdur');

const st = () => page.evaluate(() => {
  const { S, TL } = window.__editor; const p = S.hist.present; const lay = TL.layout(p);
  return { clips: TL.videoClips(p).map((c) => ({ id: c.id, srcIn: c.srcIn, srcOut: c.srcOut, start: lay.get(c.id).start, audio: TL.partnerOf(p, c) && [TL.partnerOf(p, c).srcIn, TL.partnerOf(p, c).srcOut] })),
    texts: p.clips.filter((c) => c.track === 't1').map((c) => ({ id: c.id, x: c.x, y: c.y, start: c.start })),
    subs: p.clips.filter((c) => c.track === 'c1').map((c) => ({ id: c.id, start: c.start, text: c.text })), canUndo: S.hist.canUndo };
});
const before = await st();

// 1) Yazını barmaqla sürüşdür (toxunma göstəricisi)
await page.evaluate(() => window.__editor.seek(1.0));
await page.waitForSelector('.txt');
const box = await page.locator('.txt').first().boundingBox();
const fr = await page.locator('#frame').boundingBox();
const tgt = { x: fr.x + fr.width * 0.3, y: fr.y + fr.height * 0.62 };
await page.evaluate(({ b, tgt }) => {
  const n = document.querySelector('.txt');
  const ev = (type, x, y) => n.dispatchEvent(new PointerEvent(type, { bubbles: true, pointerId: 11, pointerType: 'touch', clientX: x, clientY: y, isPrimary: true }));
  const x0 = b.x + b.width / 2, y0 = b.y + b.height / 2;
  ev('pointerdown', x0, y0);
  for (let i = 1; i <= 8; i++) ev('pointermove', x0 + (tgt.x - x0) * i / 8, y0 + (tgt.y - y0) * i / 8);
  ev('pointerup', tgt.x, tgt.y);
}, { b: box, tgt });
let s1 = await st();
const t1 = s1.texts[0];
assert.ok(Math.abs(t1.x - 0.3) < 0.02 && Math.abs(t1.y - 0.62) < 0.02, `yazı yeri: ${t1.x},${t1.y}`);
assert.deepEqual(s1.clips, before.clips, 'yazını çəkmək klipləri dəyişməməlidir');
assert.deepEqual(s1.subs, before.subs, 'yazını çəkmək subtitrləri dəyişməməlidir');
log('yazı sürüşdürüldü:', t1.x, t1.y);
await page.screenshot({ path: outJson.replace(/\.json$/, '-1-yazi.png') });

// 2) Klipi seç və sonunu toxunma ilə uzat (kəsilmiş hissə geri gəlir)
const c1 = before.clips[0];
await page.evaluate((id) => { const n = document.querySelector(`.clip[data-id="${id}"]`); const r = n.getBoundingClientRect();
  n.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 12, pointerType: 'touch', clientX: r.left + 10, clientY: r.top + 10 })); }, c1.id);
await page.waitForSelector(`.clip.sel[data-id="${c1.id}"] .h.out`);
const pps = await page.evaluate(() => window.__editor.S.pps);
await page.evaluate(({ id, dx }) => {
  const h = document.querySelector(`.clip[data-id="${id}"] .h.out`); const r = h.getBoundingClientRect();
  const x0 = r.left + r.width / 2, y = r.top + r.height / 2;
  const ev = (t, x) => (t === 'pointerdown' ? h : window).dispatchEvent(new PointerEvent(t, { bubbles: true, pointerId: 13, pointerType: 'touch', clientX: x, clientY: y }));
  ev('pointerdown', x0); for (let i = 1; i <= 10; i++) ev('pointermove', x0 + dx * i / 10); ev('pointerup', x0 + dx);
}, { id: c1.id, dx: 1.9 * pps });
let s2 = await st();
const e1 = s2.clips[0];
assert.ok(Math.abs(e1.srcOut - 5.5) < 0.08, `uzadılmış son: ${e1.srcOut}`);
assert.deepEqual(e1.audio, [e1.srcIn, e1.srcOut], 'öz səsi sinxron uzanır');
assert.ok(Math.abs(s2.clips[1].start - (before.clips[1].start + (e1.srcOut - c1.srcOut))) < 0.01, 'sonrakı klip sürüşür');
assert.ok(s2.subs.some((x) => x.text.includes('dörd')), 'geri qaytarılan sözlərin subtitri yaranır');
assert.equal(s2.texts[0].x, t1.x, 'yazının yeri qorunur');
log('klip uzadıldı:', c1.srcOut, '->', e1.srcOut, 'subtitrlər:', s2.subs.map((x) => x.text).join(' | '));
await page.screenshot({ path: outJson.replace(/\.json$/, '-2-klip.png') });

// 3) Undo / redo
await page.click('#undo');
assert.equal((await st()).clips[0].srcOut, c1.srcOut);
await page.click('#redo');
assert.equal((await st()).clips[0].srcOut, e1.srcOut);
// 4) Yenidən açanda qaralama bərpa olunur
await page.reload();
await page.waitForFunction(() => window.__editor);
assert.equal((await st()).clips[0].srcOut, e1.srcOut, 'qaralama yenidən açanda qalır');
const edits = await page.evaluate(() => window.__editor.edits());
fs.writeFileSync(outJson, JSON.stringify(edits));
log('düzəliş faylı:', Object.keys(edits.clips).length, 'klip,', Object.keys(edits.texts).length, 'yazı');
assert.deepEqual(errors, [], errors.join('; '));
await browser.close();
log('HAMISI KEÇDİ');
