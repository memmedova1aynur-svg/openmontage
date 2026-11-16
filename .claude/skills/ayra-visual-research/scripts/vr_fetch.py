#!/usr/bin/env python3
"""Seçilmiş namizədi kitabxanaya əlavə et (+ metadata + lisenziya qeydi), istəyə görə fonunu sil.

  python3 vr_fetch.py /tmp/vr/montessori 3 --folder montessori --topic "Montessori oyuncaq 2 yaş" [--cutout]

Çıxış: assets/ayra-library/<folder>/<id>.jpg (+ _cut.png), index.json yenilənir, licenses/<id>.json yazılır.
Çap edilən 'file' yolunu dizaynda istifadə et; 'attribution' sətrini caption/ilk şərhə əlavə et.
"""
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vr_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("dir"); ap.add_argument("nums", nargs="+", type=int)
ap.add_argument("--folder", default="real-photos", choices=L.FOLDERS)
ap.add_argument("--topic", default="")
ap.add_argument("--cutout", action="store_true")
a = ap.parse_args()

if a.folder == "client-portraits":
    sys.exit("Müştəri portretləri ümumi kitabxanaya düşmür — instagram-clients/<müştəri>/ qovluğunda saxla.")
cands = {m["n"]: m for m in json.loads((Path(a.dir) / "candidates.json").read_text())}
idx = L.library_index(); have = {m["id"] for m in idx}
for n in a.nums:
    m = dict(cands[n])
    if m["license"] not in L.OK_LICENSES:
        print(f"[RƏDD] #{n}: lisenziya {m['license']} kommersiya/dəyişdirmə üçün uyğun deyil"); continue
    dst = L.LIB / a.folder; dst.mkdir(parents=True, exist_ok=True)
    f = dst / f"{m['id']}.jpg"; shutil.copy(m["preview"], f)
    m.update(file=str(f.relative_to(L.LIB)), folder=a.folder, topic=a.topic or m.get("query", ""),
             attribution=L.attribution(m), restrictions=L.NOTES.get(m["license"], ""))
    m.pop("preview", None); m.pop("n", None); m.pop("local", None)
    if a.cutout:
        from rembg import new_session, remove
        from PIL import Image
        cut = remove(Image.open(f), session=new_session("isnet-general-use"))
        bbox = cut.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
        if bbox: cut = cut.crop(bbox)
        cf = L.LIB / "product-cutouts" / f"{m['id']}_cut.png"; cf.parent.mkdir(exist_ok=True); cut.save(cf)
        m["cutout"] = str(cf.relative_to(L.LIB))
    (L.LIB / "licenses").mkdir(exist_ok=True)
    (L.LIB / "licenses" / f"{m['id']}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
    if m["id"] not in have:
        idx.append(m); have.add(m["id"])
    print(json.dumps({"file": str(L.LIB / m["file"]), "cutout": str(L.LIB / m["cutout"]) if m.get("cutout") else None,
                      "attribution": m["attribution"], "restrictions": m["restrictions"]}, ensure_ascii=False))
L.save_index(idx)
