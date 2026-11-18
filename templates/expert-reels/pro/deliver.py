"""Təhvil qovluğu + fayl statusu (böyük paketlər üçün).

Status faylı: <TƏHVİL>/status.json — hər video: analiz edildi → montaj edildi → render edildi → QC keçdi | düzəliş tələb edir → təhvilə hazırdır
İstifadə:
  python3 deliver.py init  <müştəri> <tarix>                       # qovluq + boş status
  python3 deliver.py set   <müştəri> <tarix> <NN_ad> <status> [qeyd]
  python3 deliver.py add   <müştəri> <tarix> <NN_ad> <final.mp4> [--cover c.jpg] [--caption c.txt] [--qc DIR]
                           # yalnız QC KEÇDİ olan video Final Videos-a düşür; adlar eyni nömrə ilə
  python3 deliver.py report <müştəri> <tarix>                      # qısa yekun hesabat (istifadəçiyə göndərilən)
Kök: $DELIVERY_DIR (default: $MONTAJ_DATA_DIR/delivery). Orijinal videolara heç vaxt toxunulmur.
"""
import json, os, shutil, sys, time
from pathlib import Path

ROOT = Path(os.environ.get("DELIVERY_DIR", Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "delivery"))
DIRS = ["Final Videos", "Covers", "Captions", "Quality Control", "Project Files"]
ORDER = ["analiz edildi", "montaj edildi", "render edildi", "QC keçdi", "düzəliş tələb edir", "təhvilə hazırdır", "təsdiqləndi"]


def base(c, d):
    p = ROOT / c / d
    for x in DIRS: (p / x).mkdir(parents=True, exist_ok=True)
    return p


def load(p):
    f = p / "status.json"; return json.load(open(f)) if f.exists() else {}


def save(p, s): json.dump(s, open(p / "status.json", "w"), ensure_ascii=False, indent=1)


def set_status(c, d, name, st, note=""):
    assert st in ORDER, f"status: {ORDER}"
    p = base(c, d); s = load(p); e = s.setdefault(name, {"history": []})
    e["status"] = st; e["note"] = note; e["history"].append([time.strftime("%H:%M"), st, note]); save(p, s)


def add(c, d, name, mp4, cover=None, caption=None, qc=None):
    p = base(c, d); qc_ok = True
    if qc:
        qj = json.load(open(Path(qc) / "qc.json")); qc_ok = not qj["fail"]
        shutil.copytree(qc, p / "Quality Control" / name, dirs_exist_ok=True)
    if not qc_ok:
        set_status(c, d, name, "düzəliş tələb edir", "QC: " + json.dumps(qj["fail"], ensure_ascii=False)[:300]); print("QC keçməyib — Final Videos-a qoyulmadı"); return
    shutil.copy2(mp4, p / "Final Videos" / f"{name}.mp4")
    if cover: shutil.copy2(cover, p / "Covers" / f"{name}{Path(cover).suffix}")
    if caption: shutil.copy2(caption, p / "Captions" / f"{name}.txt")
    set_status(c, d, name, "təhvilə hazırdır", "")
    print("→", p / "Final Videos" / f"{name}.mp4")


def report(c, d):
    p = base(c, d); s = load(p)
    ok = [k for k, v in s.items() if v["status"] in ("təhvilə hazırdır", "təsdiqləndi")]
    bad = {k: v["note"] for k, v in s.items() if v["status"] == "düzəliş tələb edir"}
    wip = [k for k, v in s.items() if k not in ok and k not in bad]
    L = [f"Hazırlandı: {len(s)} video · QC-dən keçib, təhvilə hazır: {len(ok)}"]
    if bad: L.append("Problem qalıb: " + "; ".join(f"{k} ({v[:80]})" for k, v in bad.items()))
    if wip: L.append("Hələ işdədir: " + ", ".join(wip))
    print("\n".join(L)); return L


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if a[0] == "init": print(base(a[1], a[2]))
    elif a[0] == "set": set_status(a[1], a[2], a[3], a[4], " ".join(a[5:]))
    elif a[0] == "add":
        kw = {k: a[a.index("--" + k) + 1] for k in ("cover", "caption", "qc") if "--" + k in a}
        add(a[1], a[2], a[3], a[4], **kw)
    elif a[0] == "report": report(a[1], a[2])
