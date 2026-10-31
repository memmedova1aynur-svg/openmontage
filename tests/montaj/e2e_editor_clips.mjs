// Mərhələ 2: klip və səs (real layihənin surəti; Chromium iPhone emulyasiyası — real Safari DEYİL)
//   node tests/montaj/e2e_editor_clips.mjs <index.html> <musiqi faylı> <out.json> <asset qovluğu>
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');
const [file, music, outJson, assetDir] = process.argv.slice(2);
const log = (...a) => console.log('[klip]', ...a);
const browser = await chromium.launch();
const ctx = await browser.newContext({ ...devices['iPhone 13'] });
// claude.ai assets imkanının sınaq əvəzi: yüklənən faylı qaytarır (real səhifədə platforma edir)
await ctx.exposeFunction('__saveAsset', (b64, id) => { fs.mkdirSync(assetDir, { recursive: true }); fs.writeFileSync(path.join(assetDir, `${id}.m4a`), Buffer.from(b64, 'base64')); });
await ctx.addInitScript(() => {
  window.claude = { use: async (n) => (n === 'assets' ? { upload: async (blob) => {
    const b = new Uint8Array(await blob.arrayBuffer()); let s = ''; for (const x of b) s += String.fromCharCode(x);
    const id = 'testasset0001'; await window.__saveAsset(btoa(s), id); return { id, url: URL.createObjectURL(blob), sizeBytes: b.length, contentType: blob.type };
  } } : null) };
});
const page = await ctx.newPage();
const errors = []; page.on('pageerror', (e) => errors.push(e.message));
await page.goto('file://' + file);
await page.waitForFunction(() => window.__editor);
const st = () => page.evaluate(() => { const { S, TL } = window.__editor; const p = S.hist.present; const lay = TL.layout(p);
  return { v: TL.videoClips(p).map((c) => ({ id: c.id, srcIn: c.srcIn, srcOut: c.srcOut, start: lay.get(c.id).start, a: TL.partnerOf(p, c) && [TL.partnerOf(p, c).srcIn, TL.partnerOf(p, c).srcOut] })),
    subs: p.clips.filter((c) => c.track === 'c1').map((c) => ({ id: c.id, start: c.start, src: c.src })), music: p.clips.filter((c) => c.track === 'm1'), mix: p.mix, title: p.clips.find((c) => c.track === 't1') }; });
const tap = (sel) => page.evaluate((sel) => { const n = document.querySelector(sel); const r = n.getBoundingClientRect();
  n.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 21, pointerType: 'touch', clientX: r.left + 8, clientY: r.top + 6 })); }, sel);
const s0 = await st();

// 1) böl: oynatma xətti 20.0 s
await page.evaluate(() => window.__editor.seek(20));
await tap(`.clip[data-id="${s0.v[0].id}"]`);
await page.evaluate(() => window.__editor.seek(20));
await page.click('#sel >> text=✂ Böl');
let s1 = await st();
assert.equal(s1.v.length, 2);
assert.deepEqual([s1.v[0].srcOut, s1.v[1].srcIn], [20, 20]);
assert.ok(s1.v.every((v) => v.a && v.a[0] === v.srcIn && v.a[1] === v.srcOut), 'hər hissənin öz səsi var');
{ const a = new Set(s0.subs.map((x) => x.id)); const lost = s1.subs.filter((x) => !a.has(x.id)).length; assert.ok(lost <= 1, `bölmədən sonra ən çox 1 altyazı (sərhəddəki) dəyişir: ${lost}`); }
log('bölündü: 0–20 | 20–', s1.v[1].srcOut);

// 2) sırasını dəyiş: ikinci hissə əvvələ
await tap(`.clip[data-id="${s1.v[1].id}"]`);
await page.click('#sel button[aria-label="Sola"]');
let s2 = await st();
assert.equal(s2.v[0].id, s1.v[1].id);
const sub = s2.subs.find((x) => x.src.s >= 20);
assert.ok(Math.abs(sub.start - (sub.src.s - 20)) < 0.01, 'altyazı öz klipi ilə birlikdə hərəkət edir');
assert.ok(s2.title.start === 0 || s2.title.anchor, 'başlıq öz klipinə bağlıdır');
log('sıra dəyişdi; altyazı', sub.id, '→', sub.start);
// 3) sil və geri al
await page.click('#sel >> text=Sil');
assert.equal((await st()).v.length, 1);
await page.click('#undo');
assert.equal((await st()).v.length, 2);

// 4) musiqi əlavə et, yerini və səsini dəyiş, səviyyələr, ducking
await page.evaluate(() => { window.__editor.S.sel = null; window.__editor.S.selText = null; window.__editor.S.selAudio = null; });
await page.evaluate(() => { const r = document.querySelector('#laneS').getBoundingClientRect();
  document.querySelector('#laneS').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: r.left + 30, clientY: r.top + 4 })); });
await page.setInputFiles('#addMusic', music);
await page.waitForFunction(() => window.__editor.S.hist.present.clips.some((c) => c.track === 'm1'), null, { timeout: 10000 });
await page.click('#sel button[aria-label="Sonraya"]');
await page.evaluate(() => { const i = document.querySelector('#sel input[aria-label="Bu klipin səsi"]'); i.value = '0.4'; i.dispatchEvent(new Event('change')); });
let s4 = await st();
assert.equal(s4.music.length, 1);
assert.deepEqual([s4.music[0].start, s4.music[0].volume], [0.5, 0.4]);
// ümumi səviyyələr
await page.evaluate(() => { window.__editor.S.selAudio = null; });
await page.evaluate(() => { const r = document.querySelector('#laneS').getBoundingClientRect();
  document.querySelector('#laneS').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: r.left + 30, clientY: r.top + 4 })); });
await page.check('#duck');
await page.evaluate(() => { const i = document.querySelector('#sel input[aria-label="Musiqi"]'); i.value = '0.6'; i.dispatchEvent(new Event('change')); });
s4 = await st();
assert.equal(s4.mix.duck, true);
assert.equal(s4.mix.music, 0.6);
log('musiqi:', s4.music[0].start, 's, səs', s4.music[0].volume, '; mix', JSON.stringify(s4.mix));
const ed = await page.evaluate(() => window.__editor.edits());
assert.equal(ed.newMedia.length, 1);
fs.writeFileSync(outJson, JSON.stringify(ed));
assert.deepEqual(errors, [], errors.join('; '));
await browser.close();
log('HAMISI KEÇDİ');
