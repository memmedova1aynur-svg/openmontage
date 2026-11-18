"""Motion graphics (Remotion) — şəffaf ProRes 4444 overlay render + keş.

Komponentlər: remotion-composer/src/montaj/Motion.tsx → TitleReveal, LowerThird, QuestionCard (yay hərəkəti, maska ilə açılma,
sürətə görə hərəkət bulanıqlığı). Rəng/şrift müştərinin brand_kit.json → palette-dən gəlir.
İstifadə (modul):  path = render("LowerThird", {"name": "...", "role": "..."}, brand="<müştəri>", frames=75)
Overlay: ffmpeg -i base.mp4 -i path -filter_complex "[1:v]setpts=PTS+T/TB[o];[0:v][o]overlay=eof_action=pass"
Keş: eyni props + brend → eyni fayl (yenidən render yoxdur). 3 san ≈ 12 san CPU (ölçülüb).
Lisenziya: Remotion — fərdi şəxs və ≤3 nəfərlik şirkət üçün pulsuz; daha böyük komanda üçün şirkət lisenziyası lazımdır.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; RC = ROOT / "remotion-composer"
CACHE = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "cache" / "motion"


def brand_colors(brand):
    if not brand: return None
    p = ROOT / "instagram-clients" / brand / "brand_kit.json"
    if not p.exists(): return None
    pal = json.load(open(p)).get("palette") or {}
    if not pal: return None
    return {"ink": pal.get("ink", "#222"), "accent": pal.get("acc", "#7A1E3A"), "paper": pal.get("paper", "#FFFFFF"), "soft": pal.get("acc2", pal.get("paper2", "#EEE"))}


def ensure_fonts():
    """Şriftlər repoya düşmür (gitignore): Montserrat (Ə var) + Playfair italik montaj-data/fonts-dan kopyalanır."""
    import glob, shutil
    dst = RC / "public" / "montaj-fonts"; dst.mkdir(parents=True, exist_ok=True)
    data = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "fonts"
    for w in ("600", "700", "800"):
        s = data / f"montserrat-{w}.ttf"
        if s.exists() and not (dst / s.name).exists(): shutil.copy2(s, dst / s.name)
    if not (dst / "playfair-italic.ttf").exists():
        c = [p for p in glob.glob(str(Path.home() / ".fonts" / "nuFRD*")) + glob.glob(str(data / "*layfair*talic*"))]
        if c: shutil.copy2(c[0], dst / "playfair-italic.ttf")


def render(comp, props, brand=None, frames=None):
    ensure_fonts()
    props = dict(props); bc = brand_colors(brand)
    if bc and "brand" not in props: props["brand"] = bc
    key = hashlib.sha1(json.dumps([comp, props, frames], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True); out = CACHE / f"{comp}_{key}.mov"
    if out.exists(): return out
    pf = CACHE / f"{key}.json"; json.dump(props, open(pf, "w"), ensure_ascii=False)
    cmd = ["npx", "remotion", "render", "src/montaj/entry.tsx", comp, str(out), "--codec=prores", "--prores-profile=4444", "--image-format=png",
           "--pixel-format=yuva444p10le", f"--props={pf}", "--concurrency=4"] + ([f"--frames=0-{frames - 1}"] if frames else [])
    r = subprocess.run(cmd, cwd=RC, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-800:])
    return out


if __name__ == "__main__":
    print(render(sys.argv[1], json.loads(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None))
