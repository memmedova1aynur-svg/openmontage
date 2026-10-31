// Brauzer E2E yoxlaması (Playwright, əl ilə işə salınır):
//   MONTAJ_URL=http://localhost:4760 MEDIA_DIR=<sinxron.mp4, sukut.mp4, musiqi.wav qovluğu> OUT_DIR=<ekran şəkilləri> \
//   node tests/montaj/e2e_browser.mjs [mobile|desktop]
import { createRequire } from 'node:module';
import path from 'node:path';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');

const URL = process.env.MONTAJ_URL || 'http://localhost:4760';
const MEDIA = process.env.MEDIA_DIR;
const OUT = process.env.OUT_DIR || '.';
const mode = process.argv[2] || 'desktop';
const log = (...a) => console.log(`[${mode}]`, ...a);

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext(mode === 'mobile'
  ? { ...devices['Pixel 7'] }
  : { viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

const state = () => page.evaluate(() => {
  const { S, TL, P } = window.__montaj;
  const p = P();
  return {
    t: S.t, sel: S.sel, rev: S.revision, dirty: S.dirty, canUndo: S.hist.canUndo, canRedo: S.hist.canRedo,
    video: TL.videoClips(p).map((c) => ({ id: c.id, srcIn: c.srcIn, srcOut: c.srcOut, manual: c.manual })),
    clips: p.clips.map((c) => ({ id: c.id, track: c.track, srcIn: c.srcIn, srcOut: c.srcOut, linkedTo: c.linkedTo || null, start: c.start })),
    duration: TL.duration(p),
  };
});
const waitSaved = () => page.waitForFunction(() => !window.__montaj.S.dirty && !window.__montaj.S.saving && /Saxlanılıb/.test(document.querySelector('#saveState').textContent), null, { timeout: 15000 });

await page.goto(URL);
if (page.url().includes('/login')) {
  await page.fill('#pw', process.env.MONTAJ_PASSWORD);
  await page.click('button[type=submit]');
  await page.waitForSelector('#btnNew');
}
await page.click('details.blank-proj summary');
await page.fill('#newTitle', `E2E ${mode}`);
await page.click('#newForm button');
await page.waitForSelector('#editor:not([hidden])');
log('layihə yaradıldı');

// 1) Telefon/masaüstü: video yüklə
await page.setInputFiles('#fileInput', path.join(MEDIA, 'sinxron.mp4'));
await page.waitForSelector('.lane[data-track="v1"] .clip');
await page.waitForSelector('.lane[data-track="a1"] .clip');
let s = await state();
assert.equal(s.video.length, 1);
assert.equal(s.clips.find((c) => c.track === 'a1').linkedTo, s.video[0].id);
log('yükləndi: video + bağlı səs', s.duration);

// 2) Böl (oynatma xətti 3.55-də)
await page.evaluate(() => window.__montaj.seek(3.55));
await page.click('#tSplit');
s = await state();
assert.equal(s.video.length, 2);
assert.equal(s.clips.filter((c) => c.track === 'a1').length, 2);

// 3) İkinci hissəni seç və sil
await page.click(`.clip[data-id="${s.video[1].id}"] .lbl`);
await page.click('#tDelete');
s = await state();
assert.equal(s.video.length, 1);
assert.equal(s.video[0].srcOut, 3.55);
assert.equal(s.clips.length, 2, 'bağlı səs də silindi');
log('böl + sil: OK');

// 4) Sağ kənarı sürüyərək kəsilmiş materialı geri qaytar
const keep = s.video[0].id;
await page.evaluate(() => { window.__montaj.S.pps = 60; });
await page.click(`.clip[data-id="${keep}"] .lbl`);
const h = await page.locator(`.clip[data-id="${keep}"] .h.out`).boundingBox();
const x0 = h.x + h.width / 2;
const y0 = h.y + h.height / 2;
const dx = 2 * 60; // 2 saniyə
if (mode === 'mobile') {
  // toxunma göstəricisi ilə sürükləmə (pointerType=touch)
  await page.evaluate(({ id, x0, y0, dx }) => {
    const hnd = document.querySelector(`.clip[data-id="${id}"] .h.out`);
    const clip = hnd.closest('.clip');
    const ev = (type, x, target) => target.dispatchEvent(new PointerEvent(type, { bubbles: true, pointerId: 7, pointerType: 'touch', clientX: x, clientY: y0, isPrimary: true }));
    ev('pointerdown', x0, hnd);
    for (let i = 1; i <= 10; i++) ev('pointermove', x0 + (dx * i) / 10, clip);
    ev('pointerup', x0 + dx, clip);
  }, { id: keep, x0, y0, dx });
} else {
  await page.mouse.move(x0, y0);
  await page.mouse.down();
  for (let i = 1; i <= 10; i++) await page.mouse.move(x0 + (dx * i) / 10, y0);
  await page.mouse.up();
}
s = await state();
const ext = s.video[0].srcOut;
assert.ok(ext > 5.3 && ext < 5.8, `geri uzadılmalı idi, srcOut=${ext}`);
const au = s.clips.find((c) => c.linkedTo === keep);
assert.equal(au.srcOut, ext, 'səs də birlikdə uzandı');
log('kənarı sürüyüb geri qaytarma: srcOut', ext);

// 5) Undo / redo
await page.click('#btnUndo');
s = await state();
assert.equal(s.video[0].srcOut, 3.55);
await page.click('#btnRedo');
s = await state();
assert.equal(s.video[0].srcOut, ext);
log('undo/redo: OK');

// 6) Musiqi və mətn qatları
await page.evaluate(() => window.__montaj.seek(0));
await page.click('.lane[data-track="m1"]', { position: { x: 5, y: 10 } });
await page.setInputFiles('#fileInput', path.join(MEDIA, 'musiqi.wav'));
await page.waitForSelector('.lane[data-track="m1"] .clip', { timeout: 8000 }).catch(async (e) => { console.log('DEBUG', await page.evaluate(() => [document.querySelector('#toast').textContent, JSON.stringify(window.__montaj.P().clips.map(c=>c.track))])); await page.screenshot({ path: OUT + '/debug.png' }); throw e; });
await page.evaluate(() => window.__montaj.seek(1));
await page.click('#tText');
await page.waitForSelector('.lane[data-track="t1"] .clip', { timeout: 8000 }).catch(async (e) => {
  console.log('DEBUG', await page.evaluate(() => [document.querySelector('#toast').textContent, document.querySelector('.lane[data-track="t1"]').outerHTML.slice(0, 400)]));
  await page.screenshot({ path: OUT + '/debug.png', fullPage: true });
  throw e;
});
await page.fill('#tab-inspector textarea', 'Salam! Şəkil, ğ, ı, ö, ü, ç');
await page.locator('#tab-inspector textarea').blur();
s = await state();
assert.ok(s.clips.some((c) => c.track === 'm1'));
log('musiqi + mətn: OK');

// 7) Avtomatik saxlama və yenidən açma
await waitSaved();
const before = await state();
await page.reload();
await page.waitForSelector('.lane[data-track="v1"] .clip');
const after = await state();
assert.deepEqual(after.clips.map((c) => [c.id, c.srcIn, c.srcOut]), before.clips.map((c) => [c.id, c.srcIn, c.srcOut]));
assert.ok(after.canUndo, 'undo tarixçəsi yenidən açdıqdan sonra da var');
log('yenidən açma: OK, versiya', after.rev);

// 8) Önizləmə oynadılır, bağlı səs video elementindən səslənir
await page.evaluate(() => window.__montaj.seek(0.2));
await page.click('#btnPlay');
await page.waitForTimeout(1500);
const pv = await page.evaluate(() => ({ t: window.__montaj.S.t, vt: document.querySelector('#vid').currentTime, muted: document.querySelector('#vid').muted, playing: window.__montaj.S.playing }));
await page.click('#btnPlay');
assert.ok(pv.t > 0.8, `önizləmə irəliləməli idi: ${JSON.stringify(pv)}`);
assert.equal(pv.muted, false);
log('önizləmə:', JSON.stringify(pv));
await page.screenshot({ path: path.join(OUT, `${mode}-redaktor.png`), fullPage: mode === 'mobile' });

// 9) AI təklifi: storyboard, təsdiqdən sonra tətbiq
await page.setInputFiles('#fileInput', path.join(MEDIA, 'sukut.mp4'));
await page.waitForFunction(() => window.__montaj.TL.videoClips(window.__montaj.P()).length === 2);
await page.click('.tabs button[data-tab="ai"]');
const nBefore = (await state()).video.length;
await page.click('text=Səssiz hissələri tap');
await page.waitForSelector('text=Storyboard:', { timeout: 20000 });
assert.equal((await state()).video.length, nBefore, 'təsdiqdən əvvəl montaj dəyişmir');
await page.screenshot({ path: path.join(OUT, `${mode}-storyboard.png`), fullPage: mode === 'mobile' });
await page.click('text=Təsdiqlə və tətbiq et');
s = await state();
log('təklifdən sonra video klip sayı', nBefore, '->', s.video.length, s.video.map((v) => `${v.srcIn}-${v.srcOut}${v.manual ? '✋' : ''}`).join(' '));
assert.ok(s.video.length > nBefore);
assert.equal(s.video.find((v) => v.id === keep)?.srcOut, ext, 'əl ilə düzəldilmiş klip toxunulmadı');

// 10) MP4 ixrac
await waitSaved();
await page.click('.tabs button[data-tab="export"]');
await page.click('#tab-export button.primary');
await page.waitForSelector('#tab-export a[download]', { timeout: 120000 });
const href = await page.getAttribute('#tab-export a[download]', 'href');
log('render:', href);
await page.screenshot({ path: path.join(OUT, `${mode}-ixrac.png`), fullPage: mode === 'mobile' });
console.log(JSON.stringify({ mode, render: href, pid: (await state()) && page.url().split('/p/')[1] }));
assert.deepEqual(errors, [], 'səhifədə JS xətası olmamalıdır');
await browser.close();
log('HAMISI KEÇDİ');
