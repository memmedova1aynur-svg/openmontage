// node render.mjs <outDir> <kind> <color|-> <dur> <fps> <size>  → şəffaf PNG kadrlar f0000.png…
import { chromium } from "playwright";
import { createServer } from "http";
import { readFile } from "fs/promises";
import { mkdirSync } from "fs";
import { extname, join } from "path";

const [out, kind = "brain", color = "-", durA = "3", fpsA = "30", sizeA = "600"] = process.argv.slice(2);
const dur = +durA, fps = +fpsA, size = +sizeA;
mkdirSync(out, { recursive: true });
const root = new URL(".", import.meta.url).pathname;
const types = { ".html": "text/html", ".js": "text/javascript" };
const srv = createServer(async (req, res) => {
  try { const p = join(root, decodeURIComponent(req.url.split("?")[0]));
    res.writeHead(200, { "content-type": types[extname(p)] || "application/octet-stream" }); res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(r => srv.listen(0, "127.0.0.1", r));
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", e => errs.push(e.message));
await page.goto(`http://127.0.0.1:${srv.address().port}/index.html?kind=${kind}&size=${size}&color=${color === "-" ? "" : color.replace("#", "")}`);
await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 }).catch(() => {});
if (errs.length) { console.error("page error:", errs.join("; ")); await browser.close(); srv.close(); process.exit(1); }
const n = Math.max(1, Math.round(dur * fps));
for (let i = 0; i < n; i++) {
  await page.evaluate(([t, d]) => window.renderAt(t, d), [i / fps, dur]);
  await page.screenshot({ path: join(out, `f${String(i).padStart(4, "0")}.png`), omitBackground: true });
}
await browser.close(); srv.close();
console.log(`done: ${n}`);
