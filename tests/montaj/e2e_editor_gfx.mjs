// Peşəkar qrafika + altyazı düzəlişi (real layihə, Chromium iPhone emulyasiyası — real Safari DEYİL)
import { createRequire } from 'node:module';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');
const [file, outJson, shotDir] = process.argv.slice(2);
const log = (...a) => console.log('[qrafika]', ...a);
const browser = await chromium.launch();
const page = await (await browser.newContext({ ...devices['iPhone 13'] })).newPage();
const errors = []; page.on('pageerror', (e) => errors.push(e.message));
await page.goto('file://' + file);
await page.waitForFunction(() => window.__editor);
const P = () => page.evaluate(() => window.__editor.S.hist.present);
const base = await P();
const sig = (p, skip) => JSON.stringify(p.clips.filter((c) => !skip.includes(c.id)).sort((a, b) => (a.id < b.id ? -1 : 1)).map((c) => [c.id, c.start, c.srcIn, c.srcOut, c.text, c.bg, c.color, c.size, c.volume, c.frame]));
const seek = (t) => page.evaluate((t) => window.__editor.seek(t), t);

// 1) qrafikalar kadrda görünür (MG ilə)
for (const t of [1.2, 8.5, 19.0, 27.0]) { await seek(t); await page.waitForTimeout(150); await page.screenshot({ path: `${shotDir}/gfx-${t}.png` }); }
await seek(8.5);
assert.ok(await page.$('#texts .gfx'), 'qrafika elementi görünməlidir');

// 2) altyazı: bir sözü düzəlt (söz düyməsi → yalnız burada)
const bad = base.clips.find((c) => c.type === 'caption' && /enişək/.test(c.text));
assert.ok(bad, 'səhv altyazı tapılmalıdır');
await seek((await page.evaluate((id) => window.__editor.TL.layout(window.__editor.S.hist.present).get(id).start, bad.id)) + 0.05);
await page.click(`[data-tid="${bad.id}"]`);
const wi = bad.words.findIndex((w) => /enişək/.test(w.w));
await page.click(`#sel .words button >> nth=${wi}`);
await page.fill('#sel input[aria-label="Seçilmiş sözün düzgün yazılışı"]', 'eyni şey');
await page.click('#sel >> text=Yalnız burada düzəlt');
let p = await P();
const fixed = p.clips.find((c) => c.id === bad.id);
assert.match(fixed.text, /eyni şey/);
assert.equal(fixed.start, bad.start); assert.equal(fixed.srcOut - fixed.srcIn, bad.srcOut - bad.srcIn, 'vaxt dəyişməməlidir');
assert.equal(sig(p, [bad.id]), sig(base, [bad.id]), 'qalan montaj dəyişməməlidir');
log('altyazı düzəldi:', fixed.text);

// 3) kart görünüşü: fon və mətn rəngi
const card = p.clips.find((c) => c.type === 'card');
await seek((await page.evaluate((id) => window.__editor.TL.layout(window.__editor.S.hist.present).get(id).start, card.id)) + 1);
await page.click(`[data-tid="${card.id}"]`);
const before = await P();
await page.evaluate((id) => { const E = window.__editor; E.commit(E.TL.setTextProps(E.S.hist.present, id, { bg: '#FFFFFF@0.92', color: '#1E1D12' }), 'test'); }, card.id);
p = await P();
const c2 = p.clips.find((c) => c.id === card.id);
assert.equal(c2.bg, '#FFFFFF@0.92'); assert.equal(c2.color, '#1E1D12');
assert.equal(sig(p, [card.id]), sig(before, [card.id]), 'qalan montaj dəyişməməlidir');
await page.waitForTimeout(150);
await page.screenshot({ path: `${shotDir}/card-changed.png` });
log('kart dəyişdi');

// 4) undo/redo
await page.click('#undo'); assert.notEqual((await P()).clips.find((c) => c.id === card.id).bg, '#FFFFFF@0.92');
await page.click('#redo'); assert.equal((await P()).clips.find((c) => c.id === card.id).bg, '#FFFFFF@0.92');

const ed = await page.evaluate(() => window.__editor.edits());
fs.writeFileSync(outJson, JSON.stringify(ed));
log('düzəliş: dəyişən', ed.changed.length);
assert.deepEqual(errors, [], errors.join('; '));
await browser.close();
log('HAMISI KEÇDİ');
