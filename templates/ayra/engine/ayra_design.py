#!/usr/bin/env python3
"""AYRA Professional Design Engine — vahid render və yoxlama aləti (yerli, API-siz).

  ayra_design.py render <page.html> <out-basename> --size reels|story|post|highlight|poster|WxH [--fmt png,jpg,pdf,svg] [--spec spec.json]
  ayra_design.py preview <img1.png> [img2 ...] --out sheet.jpg      # tam + 3:4 grid kəsimi + 270px thumbnail (yan-yana)
  ayra_design.py grid <img1..img9> --out grid.jpg                   # Instagram profil grid simulyasiyası (3 sütun, 3:4)
  ayra_design.py animate <page.html> <out.mp4> --size story --dur 10 [--fps 30] [--gif out.gif]
       (səhifədə window.seek(t) və window.ready=true olmalıdır; GSAP timeline-ı t-yə çəkir)
  ayra_design.py fontcheck <font.ttf> [--text "..."]

HTML: <html lang="az"> MƏCBURİ. {{açar}} yer tutucuları --spec JSON-dan doldurulur (fayl yolları file:// olur).
data-check="ad" atributlu elementlər kənara 56px-dən yaxınlıq və mətn daşması üçün yoxlanır.
PDF vektor qalır (Playwright print); SVG = PDF → Inkscape (mətn əyriyə çevrilir, redaktə üçün)."""
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
SIZES = {"reels": (1080, 1920), "story": (1080, 1920), "post": (1080, 1350), "carousel": (1080, 1350), "highlight": (1080, 1080), "poster": (1240, 1754)}
CHROME = "/opt/pw-browsers/chromium"

def size(s):
    if s in SIZES: return SIZES[s]
    w, h = s.lower().split("x"); return int(w), int(h)

def fill(html, spec):
    def v(m):
        x = str(spec.get(m.group(1), m.group(0)))
        return Path(x).resolve().as_uri() if os.path.exists(x) and Path(x).suffix.lower() in (".png", ".jpg", ".jpeg", ".svg", ".ttf", ".otf", ".css", ".js", ".json", ".mp4") else x
    return re.sub(r"\{\{(\w+)\}\}", v, html)

def page_file(src, spec):
    html = Path(src).read_text()
    if 'lang="az"' not in html: print("XƏBƏRDARLIQ: <html lang=\"az\"> yoxdur — böyük hərf İ/I səhv çıxa bilər")
    if spec: html = fill(html, json.load(open(spec)))
    left = sorted(set(re.findall(r"\{\{(\w+)\}\}", html)))
    if left: print("XƏBƏRDARLIQ: doldurulmamış:", left)
    # nisbi yollar orijinal qovluğa görə qalsın
    t = Path(src).resolve().parent / (".render_" + Path(src).name); t.write_text(html); return t

CHECK_JS = """() => [...document.querySelectorAll('[data-check]')].flatMap(e => { const r = e.getBoundingClientRect(), o = [];
  if (r.width && (r.left < 56 || r.top < 56 || r.right > innerWidth - 56 || r.bottom > innerHeight - 56)) o.push(e.dataset.check + ': kənara 56px-dən yaxın');
  if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflow == 'hidden') o.push(e.dataset.check + ': mətn sığmır'); return o; })"""

def render(a):
    from playwright.sync_api import sync_playwright
    W, H = size(a.size); f = page_file(a.page, a.spec); fmts = a.fmt.split(","); out = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(f.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
        for o in pg.evaluate(CHECK_JS): print("YOXLAMA:", o)
        if "png" in fmts: pg.screenshot(path=a.out + ".png"); out.append(a.out + ".png")
        if "jpg" in fmts: pg.screenshot(path=a.out + ".jpg", type="jpeg", quality=93); out.append(a.out + ".jpg")
        if "pdf" in fmts or "svg" in fmts:
            pg.pdf(path=a.out + ".pdf", width=f"{W}px", height=f"{H}px", print_background=True, page_ranges="1"); out.append(a.out + ".pdf")
        b.close()
    if "svg" in fmts:
        subprocess.run(["inkscape", a.out + ".pdf", "--export-type=svg", "--export-text-to-path", "-o", a.out + ".svg"], capture_output=True); out.append(a.out + ".svg")
        if "pdf" not in fmts: os.remove(a.out + ".pdf"); out.remove(a.out + ".pdf")
    f.unlink(missing_ok=True); print("\n".join(out))

def preview(a):
    from PIL import Image, ImageDraw
    rows = []
    for pth in a.imgs:
        im = Image.open(pth).convert("RGB"); W, H = im.size; th = 900
        full = im.resize((int(W * th / H), th))
        crop = im.crop((0, max(0, (H - W * 4 // 3) // 2), W, max(0, (H - W * 4 // 3) // 2) + W * 4 // 3)) if H > W * 4 // 3 else im
        g = crop.resize((int(crop.width * th / crop.height), th)); t = im.resize((270, int(270 * H / W)))
        row = Image.new("RGB", (full.width + g.width + 330 + 60, th + 40), "white"); d = ImageDraw.Draw(row)
        row.paste(full, (10, 30)); row.paste(g, (full.width + 30, 30)); row.paste(t, (full.width + g.width + 50, 30))
        d.text((10, 8), f"{Path(pth).name} — tam", fill="black"); d.text((full.width + 30, 8), "profil grid 3:4", fill="black"); d.text((full.width + g.width + 50, 8), "telefon 270px", fill="black")
        rows.append(row)
    S = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), "white"); y = 0
    for r in rows: S.paste(r, (0, y)); y += r.height
    S.save(a.out, quality=90); print(a.out)

def grid(a):
    from PIL import Image
    tw, th, gap = 360, 480, 4; ims = a.imgs[:9]; rows = (len(ims) + 2) // 3
    S = Image.new("RGB", (3 * tw + 2 * gap, rows * th + (rows - 1) * gap), "white")
    for i, pth in enumerate(ims):
        im = Image.open(pth).convert("RGB"); W, H = im.size; ch = W * 4 // 3
        im = im.crop((0, (H - ch) // 2, W, (H - ch) // 2 + ch)) if H > ch else im.crop(((W - H * 3 // 4) // 2, 0, (W - H * 3 // 4) // 2 + H * 3 // 4, H))
        S.paste(im.resize((tw, th)), ((i % 3) * (tw + gap), (i // 3) * (th + gap)))
    S.save(a.out, quality=90); print(a.out)

def animate(a):
    from playwright.sync_api import sync_playwright
    W, H = size(a.size); f = page_file(a.page, a.spec); d = Path(tempfile.mkdtemp()); n = int(a.dur * a.fps)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": W, "height": H}); pg.goto(f.as_uri())
        pg.wait_for_function("window.ready===true", timeout=20000); pg.evaluate("document.fonts.ready")
        for i in range(n): pg.evaluate(f"seek({i / a.fps})"); pg.screenshot(path=str(d / f"{i:05d}.png"))
        b.close()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", str(d / "%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "medium", "-movflags", "+faststart", a.out], check=True)
    if a.gif:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.out, "-vf", "fps=15,scale=540:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer", a.gif], check=True)
    f.unlink(missing_ok=True); print(a.out, f"{n} kadr", a.gif or "")

def fontcheck(a):
    from fontTools.ttLib import TTFont
    AZ = "ƏəĞğİıŞşÇçÖöÜü"; cm = TTFont(a.font).getBestCmap(); miss = [c for c in AZ if ord(c) not in cm]
    print(a.font, "Azərbaycan hərfləri:", "TAM" if not miss else "ÇATMIR " + "".join(miss))
    if a.text:
        up = a.text.replace("i", "İ").replace("ı", "I").upper(); bad = sorted({c for c in a.text + up if not c.isspace() and ord(c) not in cm})
        print("mətn:", "OK" if not bad else "dəstəklənmir: " + "".join(bad), "| az böyük hərf:", up)

ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
r = sp.add_parser("render"); r.add_argument("page"); r.add_argument("out"); r.add_argument("--size", default="reels"); r.add_argument("--fmt", default="png"); r.add_argument("--spec")
pv = sp.add_parser("preview"); pv.add_argument("imgs", nargs="+"); pv.add_argument("--out", required=True)
gr = sp.add_parser("grid"); gr.add_argument("imgs", nargs="+"); gr.add_argument("--out", required=True)
an = sp.add_parser("animate"); an.add_argument("page"); an.add_argument("out"); an.add_argument("--size", default="story"); an.add_argument("--dur", type=float, default=10)
an.add_argument("--fps", type=int, default=30); an.add_argument("--gif"); an.add_argument("--spec")
fc = sp.add_parser("fontcheck"); fc.add_argument("font"); fc.add_argument("--text")
a = ap.parse_args(); {"render": render, "preview": preview, "grid": grid, "animate": animate, "fontcheck": fontcheck}[a.cmd](a)
