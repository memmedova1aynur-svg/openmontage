"""Redaktor sınağı üçün sintetik layihə: 12 s çaxma+siqnal videosu, saxta söz vaxtları,
iki kart (0.5–3.6 və 6.5–9.6), birinci kartda ekran yazısı, subtitr açıq."""

from __future__ import annotations

import os
import sys
from pathlib import Path

WORDS = [{"w": w, "s": float(i), "e": i + 0.4} for i, w in enumerate(
    ["sıfır", "bir", "iki", "üç", "dörd", "beş", "altı", "yeddi", "səkkiz", "doqquz", "on", "on bir"])][1:]


def make(data_dir: Path, media_dir: Path) -> str:
    os.environ["MONTAJ_DATA_DIR"] = str(data_dir)
    os.environ.setdefault("MONTAJ_SYNC_DERIVE", "1")
    from montaj import server, session, store
    from tests.montaj.test_montaj import make_sync_source

    src = media_dir / "sinxron.mp4"
    if not src.is_file():
        make_sync_source(src)
    base = session.node_tl("migrate", session.node_tl("newProject", {"id": "tmp", "title": "Redaktor sınağı"}))
    p = store.create("Redaktor sınağı", base)
    pid = p["id"]
    tmp = store.originals_dir(pid) / ".fx.part"
    tmp.write_bytes(src.read_bytes())
    m = server._register(pid, tmp, "sinxron.mp4")["media"]
    p = store.load(pid)
    p.update(aspect="9:16", width=202, height=360)
    sb = {"subtitles": True, "candidates": {m["id"]: [{"words": WORDS}]}, "cards": [
        {"id": "c1", "mediaId": m["id"], "srcIn": 0.5, "srcOut": 3.6, "include": True, "onScreenText": "Vacib mövzu",
         "words": [w for w in WORDS if 0.5 <= w["s"] and w["e"] <= 3.6]},
        {"id": "c2", "mediaId": m["id"], "srcIn": 6.5, "srcOut": 9.6, "include": True,
         "words": [w for w in WORDS if 6.5 <= w["s"] and w["e"] <= 9.6]},
    ]}
    frame = {"aspect": "9:16", "mode": "auto", "s": 1, "baseW": (9 / 16 * 360) / 640, "baseH": 1,
             "keys": [{"t": 0, "cx": 0.5, "cy": 0.5}], "rotate": 0}
    r = session.node_tl("applyStoryboard", session.node_tl("migrate", p), sb, {"frames": {m["id"]: frame}})
    store.save(pid, r["project"], p["revision"])
    return pid


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    print(make(Path(sys.argv[1]), Path(sys.argv[2])))
