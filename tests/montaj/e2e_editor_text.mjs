// Mərhələ 1: yazı/altyazı idarəsi (real layihə, Chromium iPhone emulyasiyası — real Safari DEYİL)
import { createRequire } from 'node:module';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');
const [file, outJson, shotDir] = process.argv.slice(2);
const log = (...a) => console.log('[yazı]', ...a);
const browser = await chromium.launch();
const page = await (await browser.newContext({ ...devices['iPhone 13'] })).newPage();
const errors = []; page.on('pageerror', (e) => errors.push(e.message));
await page.goto('file://' + file);
await page.waitForFunction(() => window.__editor);
const P = () => page.evaluate(() => window.__editor.S.hist.present);
const base = await P();
const title = base.clips.find((c) => c.track === 't1');
const subs = base.clips.filter((c) => c.track === 'c1');
const others = (p, ids) => JSON.stringify(p.clips.filter((c) => !ids.includes(c.id)).map((c) => [c.id, c.start, c.srcIn, c.srcOut, c.text, c.color, c.font]));

// 1) altyazının mətnini düzəlt (yalnız o dəyişir)
const bad = subs.find((c) => /enişək/.test(c.text));
assert.ok(bad, 'səhv tanınmış altyazı tapılmalıdır');
await page.click(`[data-tid="${bad.id}"]`);
await page.waitForSelector('#sel textarea');
await page.fill('#sel textarea', bad.text.replace('enişək', 'eyni şey'));
await page.locator('#sel textarea').blur();
let p = await P();
assert.equal(p.clips.find((c) => c.id === bad.id).text, bad.text.replace('enişək', 'eyni şey'));
assert.equal(others(p, [bad.id]), others(base, [bad.id]), 'digər elementlər dəyişməməlidir');
log('altyazı mətni düzəldi:', p.clips.find((c) => c.id === bad.id).text);

// 2) bütün altyazıların rəngi sarı (əl ilə dəyişən altyazı öz üslubunu saxlayır)
await page.click('#sel button[aria-label="Rəng #F4D77A"] >> nth=1');
p = await P();
assert.equal(p.subtitles.style.color, '#F4D77A');
assert.ok(p.clips.filter((c) => c.track === 'c1' && !c.manual).every((c) => c.color === '#F4D77A'));
log('bütün altyazılar sarı');

// 3) başlıq: şrift Caveat, fonsuz, ölçü, vaxt +1 s
await page.click(`[data-tid="${title.id}"]`);
await page.selectOption('#sel select[aria-label="Şrift"]', 'Caveat');
await page.click('#sel >> text=Fonsuz');
await page.evaluate(() => { const i = document.querySelector('#sel input[aria-label="Ölçü"]'); i.value = '0.08'; i.dispatchEvent(new Event('change')); });
await page.click('#sel button[aria-label="Müddəti 1 s artır"]');
p = await P();
const t = p.clips.find((c) => c.id === title.id);
assert.deepEqual([t.font, t.bg, t.srcOut], ['Caveat', 'none', 4]); assert.ok(Math.abs(t.size - 0.08) < 0.003);
log('başlıq:', t.font, t.bg, t.size, `${t.srcOut} s`);
await page.evaluate(() => window.__editor.seek(1));
await page.waitForTimeout(500);
await page.screenshot({ path: `${shotDir}/stage1-editor.png` });

// 4) yeni yazı əlavə et, bir altyazını sil, undo/redo
await page.evaluate(() => { const r = document.querySelector('#laneT').getBoundingClientRect(); const pps = window.__editor.S.pps;
  document.querySelector('#laneT').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: r.left + 10 * pps, clientY: r.top + 5 })); });
const n0 = (await P()).clips.length;
await page.evaluate(() => { const b = [...document.querySelectorAll('#sel button')].find((x) => x.textContent.includes('Yazı əlavə et')); b && b.click(); });
p = await P();
assert.equal(p.clips.length, n0 + 1);
const del = subs[3];
await page.click(`[data-tid="${del.id}"]`);
await page.click('#sel >> text=Sil');
p = await P();
assert.ok(!p.clips.some((c) => c.id === del.id) && p.subtitles.removed.includes(del.id), 'altyazı silindi və yenidən yaranmır');
await page.click('#undo');
assert.ok((await P()).clips.some((c) => c.id === del.id));
await page.click('#redo');
assert.ok(!(await P()).clips.some((c) => c.id === del.id));
const ed = await page.evaluate(() => window.__editor.edits());
assert.equal(ed.schema, 2);
fs.writeFileSync(outJson, JSON.stringify(ed));
log('düzəliş faylı: dəyişən', ed.changed.length, 'silinən', ed.removed.length);
assert.deepEqual(errors, [], errors.join('; '));
await browser.close();
log('HAMISI KEÇDİ');
