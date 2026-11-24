// Deterministic frame capture: node render.mjs <outDir> <fps> <t0> <t1> [step]
// With step>0 renders only every `step` seconds (stills for review).
import { chromium } from "playwright";
import { createServer } from "http";
import { readFile } from "fs/promises";
import { mkdirSync } from "fs";
import { extname, join } from "path";

const [out = "frames", fpsArg = "30", t0Arg = "0", t1Arg = "25", stepArg = "0"] = process.argv.slice(2);
const fps = +fpsArg, t0 = +t0Arg, t1 = +t1Arg, step = +stepArg;
mkdirSync(out, { recursive: true });
const root = new URL(".", import.meta.url).pathname;
const types = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".woff2": "font/woff2" };
const srv = createServer(async (req, res) => {
  try { const p = join(root, decodeURIComponent(req.url.split("?")[0]).replace(/^\/$/, "/index.html"));
    res.writeHead(200, { "content-type": types[extname(p)] || "application/octet-stream" }); res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
}).listen(8899, "127.0.0.1");

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on("console", m => { if (m.type() === "error") console.error("page:", m.text()); });
page.on("pageerror", e => console.error("pageerror:", e.message));
await page.goto("http://127.0.0.1:8899/index.html");
await page.waitForFunction(() => window.renderAt && window.ready);
await page.evaluate(() => window.ready);
const times = [];
if (step > 0) for (let t = t0; t <= t1 + 1e-9; t += step) times.push(+t.toFixed(3));
else for (let f = Math.round(t0 * fps); f < Math.round(t1 * fps); f++) times.push(f / fps);
let i = 0; const start = Date.now();
for (const t of times) {
  await page.evaluate(tt => window.renderAt(tt), t);
  const name = step > 0 ? `t${t.toFixed(2)}.jpg` : `f${String(Math.round(t * fps)).padStart(5, "0")}.jpg`;
  await page.screenshot({ path: join(out, name), type: "jpeg", quality: 93 });
  if (++i % 60 === 0) console.log(`${i}/${times.length} frames, ${((Date.now() - start) / i).toFixed(0)} ms/frame`);
}
await browser.close(); srv.close();
console.log(`done: ${times.length} frames -> ${out}`);
