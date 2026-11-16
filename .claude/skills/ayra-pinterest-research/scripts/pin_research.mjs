#!/usr/bin/env node
// AYRA Pinterest research — Pinterest MCP kitabxanasını (@sunkimkk/pinterest-mcp@1.2.0, MIT) birbaşa çağırır.
// Login/API açarı yoxdur. Yalnız REFERANS üçündür — pin şəkilləri yekun dizayna qoyulmur.
//
//   node pin_research.mjs --out <dir> --n 20 "editorial instagram post pink" "premium carousel design"
//
// Nəticə: <dir>/pins.json (metadata) + <dir>/p/NN.jpg (474px önizləmə). Sonra:  python3 pin_sheet.py <dir>
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
const here = path.dirname(new URL(import.meta.url).pathname);
let lib;
try {
  lib = await import(path.join(here, 'node_modules/@sunkimkk/pinterest-mcp/src/pinterest.js'));
} catch {
  console.error('Quraşdırılmayıb. İşlət:  (cd ' + here + ' && npm i @sunkimkk/pinterest-mcp@1.2.0)');
  process.exit(2);
}
const args = process.argv.slice(2);
const opt = { out: null, n: 20 };
const queries = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--out') opt.out = args[++i];
  else if (args[i] === '--n') opt.n = +args[++i];
  else queries.push(args[i]);
}
if (!opt.out || !queries.length) { console.error('usage: --out DIR [--n 20] "query" ...'); process.exit(1); }
await fs.mkdir(path.join(opt.out, 'p'), { recursive: true });
const seen = new Set(); const pins = [];
for (const q of queries) {
  try {
    const r = await lib.searchPins(q, { limit: opt.n });
    for (const p of r.pins || []) {
      const key = p.pin_id || p.id || p.url || p.image_url;
      if (!p.image_url || seen.has(key)) continue;
      seen.add(key); pins.push({ ...p, query: q });
    }
    console.error(`"${q}": ${r.pins?.length ?? 0}`);
  } catch (e) { console.error(`[!] "${q}": ${e.message}`); }
}
let k = 0;
for (const p of pins) {
  try {
    const pr = await lib.fetchPreview(p.image_url, '474x');
    const buf = pr.buf || (pr.data ? Buffer.from(pr.data, 'base64') : null);
    if (!buf) throw new Error('boş önizləmə');
    p.n = k; p.preview = path.join(opt.out, 'p', `${String(k).padStart(2, '0')}.jpg`);
    await fs.writeFile(p.preview, buf); k++;
  } catch (e) { p.error = e.message; }
}
const ok = pins.filter((p) => p.preview);
await fs.writeFile(path.join(opt.out, 'pins.json'), JSON.stringify(ok, null, 1));
console.log(`${ok.length} pin önizləməsi → ${opt.out}`);
