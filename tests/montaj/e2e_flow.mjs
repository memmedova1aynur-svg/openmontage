// v2 telefon axını E2E (Playwright/Chromium, iPhone ölçüsü emulyasiyası — real Safari DEYİL):
//   MONTAJ_URL=http://localhost:4760 MONTAJ_PASSWORD=... MEDIA_DIR=... OUT_DIR=... NODE_PATH=$(npm root -g) node tests/montaj/e2e_flow.mjs
import { createRequire } from 'node:module';
import path from 'node:path';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');
const URL = process.env.MONTAJ_URL || 'http://localhost:4760';
const MEDIA = process.env.MEDIA_DIR;
const OUT = process.env.OUT_DIR || '.';
const PW = process.env.MONTAJ_PASSWORD;
const log = (...a) => console.log('[flow]', ...a);
const shot = (page, n, full = true) => page.screenshot({ path: path.join(OUT, `flow-${n}.png`), fullPage: full });

const browser = await chromium.launch();
const ctx = await browser.newContext({ ...devices['iPhone 13'] });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

// 1) Giriş
await page.goto(URL);
await page.waitForURL(/\/login$/);
await page.fill('#pw', 'səhv');
await page.click('button[type=submit]');
await page.waitForSelector('#err:has-text("Parol səhvdir")');
await page.fill('#pw', PW);
await page.click('button[type=submit]');
await page.waitForSelector('#btnNew');
log('giriş: OK');

// 2) Material: video + şəkil
await page.click('#btnNew');
await page.fill('#flowTitle', 'Telefon testi');
await page.setInputFiles('#srcFiles', [path.join(MEDIA, 'sinxron.mp4'), path.join(MEDIA, 'sukut.mp4'), path.join(MEDIA, 'foto.jpg')]);
await page.waitForFunction(() => document.querySelectorAll('#srcItems li').length === 3 && [...document.querySelectorAll('#srcItems li')].every((li) => li.textContent.includes('hazırdır')), null, { timeout: 60000 });
// səhv Drive linki: aydın xəta
await page.fill('#driveLinks', 'https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz0');
await page.click('text=Linki əlavə et');
await page.waitForSelector('#srcItems li.err:has-text("Qovluq linki")');
await shot(page, '1-material');
log('material: OK');

// 3) Müştəri
await page.click('#toClient');
await page.waitForSelector('text=Kimin videosudur?');
await page.fill('input[type=search]', 'nərgiz');
const names = await page.$$eval('.client-list li', (l) => l.map((x) => x.textContent));
assert.equal(names.length, 1);
await shot(page, '2-musteri', false);
assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'səhifə ekrandan enli olmamalıdır');
await page.click('.client-list button');
await page.waitForSelector('text=Rəng kodları qeyd olunmayıb.');
await page.click('text=Dəyişiklik et');
await page.fill('input[placeholder="#1A2B3C, #FFFFFF"]', '#1A2B3C, #F2C94C');
await page.click('text=Yalnız bu layihəyə tətbiq et');
await page.waitForSelector('text=Montaj seçimləri');
log('müştəri: OK');

// 4) Seçimlər
await page.click('.chip:has-text("Talking-head")');
await page.click('.chip:has-text("Reklam / satış")');
assert.equal(await page.$$eval('.chip.on', (l) => l.filter((x) => x.textContent === 'Talking-head').length), 1);
assert.ok(await page.isDisabled('.chip:has-text("Səsləndirmə (qoşulmayıb)")'), 'qoşulmayan xidmət aktiv görünməməlidir');
await page.fill('input[aria-label="Müddət (saniyə)"]', '20');
await page.locator('input[aria-label="Müddət (saniyə)"]').blur();
await shot(page, '3-secimler');
await page.click('#makeSb');
await page.waitForSelector('#approveSb', { timeout: 300000 });
await page.waitForSelector('text=Qaydalara əsaslanan təklif');
await shot(page, '4-storyboard');
const nCards = await page.$$eval('.sb-card', (l) => l.length);
assert.equal(nCards, 4, `kart sayı ${nCards}`);
log('storyboard kartları:', nCards);

// tək kart: alternativ (digər kartlar dəyişmir)
const before = await page.$$eval('.sb-card .meta', (l) => l.map((x) => x.textContent));
const idx = before.findIndex((t, i) => i > 0 && t.includes('sukut.mp4') && before[i - 1].includes('sukut.mp4'));
assert.ok(idx > 0, 'iki hissəli mənbə tapılmalıdır');
await page.locator('.sb-card').nth(idx).locator('text=Alternativ göstər').click();
await page.waitForFunction(([b, i]) => {
  const now = [...document.querySelectorAll('.sb-card .meta')].map((x) => x.textContent);
  return now[i] !== b[i];
}, [before, idx]);
const after = await page.$$eval('.sb-card .meta', (l) => l.map((x) => x.textContent));
assert.ok(after[idx].includes('Əvvəlki hissə ilə birlikdə'), after[idx]);
after.forEach((t, i) => { if (i !== idx) assert.equal(t, before[i], 'digər kartlar dəyişməməlidir'); });
// ekranda mətn yaz
await page.locator('.sb-card').first().locator('text=Bu hissəni dəyiş').click();
await page.fill('.modal-card input >> nth=0', 'Bu gün vacib mövzu');
await page.click('.modal-card >> text=Saxla');
await page.waitForSelector('.sb-card .ost:has-text("Bu gün vacib mövzu")');
// yenidən aç: storyboard bərpa olunur
await page.waitForTimeout(1200);
await page.reload();
await page.waitForSelector('#approveSb');
assert.ok(await page.$('.sb-card .ost:has-text("Bu gün vacib mövzu")'), 'storyboard düzəlişi yenidən açanda qalır');
log('storyboard düzəlişi + bərpa: OK');

// 5) Təsdiq -> montaj
await page.click('#approveSb');
await page.waitForSelector('#editor:not([hidden]) .lane[data-track="v1"] .clip');
const st = await page.evaluate(() => {
  const { TL, P } = window.__montaj;
  const p = P();
  return { w: p.width, h: p.height, aspect: p.aspect, v: TL.videoClips(p).length, t: p.clips.filter((c) => c.track === 't1').length, framed: TL.videoClips(p).filter((c) => c.frame).length };
});
log('montaj:', JSON.stringify(st));
assert.equal(st.aspect, '9:16');
assert.ok(st.h > st.w);
assert.ok(st.t >= 1, 'ekrandakı mətn klipi yaradılmalıdır');
await shot(page, '5-redaktor');

// 6) Kadraj, görüntü, qrafika
await page.click('.tabs button[data-tab="frame"]');
await page.waitForSelector('#tab-frame:has-text("Çıxış formatı")');
await page.evaluate(() => { const { TL, P, S } = window.__montaj; S.sel = TL.videoClips(P())[0].id; });
await page.click('.tabs button[data-tab="look"]');
await page.click('.tabs button[data-tab="frame"]');
const sl = page.locator('#tab-frame input[aria-label="Üfüqi yer"]');
await sl.fill('0.3');
await sl.dispatchEvent('change');
const fr = await page.evaluate(() => window.__montaj.TL.videoClips(window.__montaj.P())[0].frame);
assert.equal(fr.mode, 'manual');
await shot(page, '6-kadraj');
await page.click('.tabs button[data-tab="look"]');
await page.check('#tab-look input[type=checkbox] >> nth=1');
const adj = await page.evaluate(() => window.__montaj.TL.videoClips(window.__montaj.P())[0].adjust);
assert.equal(adj.mirror, true);
await page.click('.tabs button[data-tab="graphics"]');
await page.check('#tab-graphics label:has-text("Animasiyalı sonluq") input');
await page.fill('#tab-graphics input[placeholder="məs. Qeydiyyat üçün yazın"]', 'Bizə yazın');
await page.locator('#tab-graphics input[placeholder="məs. Qeydiyyat üçün yazın"]').blur();
log('kadraj/görüntü/qrafika: OK');

// 7) Paylaş
await page.click('.tabs button[data-tab="share"]');
await page.click('#tab-share >> text=MP4 hazırla');
await page.waitForSelector('#tab-share video.share-video', { timeout: 180000 });
await page.fill('#tab-share textarea', 'Test caption');
await page.locator('#tab-share textarea').blur();
const dl = await page.getAttribute('#tab-share a:has-text("MP4 endir")', 'href');
assert.match(dl, /download=1/);
await page.waitForSelector('#tab-share button:has-text("Paylaş")');
await shot(page, '7-paylas');
const shareState = await page.evaluate(() => ({ canShare: typeof navigator.canShare, share: typeof navigator.share }));
log('paylaş ekranı: OK', JSON.stringify(shareState), dl);
const resp = await page.request.get(URL + dl);
assert.equal(resp.status(), 200);
const buf = await resp.body();
assert.ok(buf.length > 10000);
console.log(JSON.stringify({ render: dl, size: buf.length }));
assert.deepEqual(errors, [], 'JS xətası olmamalıdır: ' + errors.join('; '));
await browser.close();
log('HAMISI KEÇDİ');
