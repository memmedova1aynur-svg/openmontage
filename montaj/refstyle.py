"""Referans öyrənməsi: bəyənilən montaj nümunəsindən QƏRARLARI çıxar (kopyalama yox), fərqli mövzulara tətbiq et.

Yerli, pulsuz (ffmpeg): kəsim ritmi (kəsim sayı, plan uzunluqları, ilk 3 s tempi), səs (səs səviyyəsi, sükut payı),
kadr kontakt şəkli (baxıb qərar çıxarmaq üçün; REPOYA yazılmır). Yalnız ölçülər və agentin çıxardığı qərarlar `montaj/references/<ad>.json`-a yazılır —
referans videonun özü, kadrları və transkripti repoya yüklənmir (müəllif hüququ/şəxsi məlumat).
Agent kontakt şəklinə baxıb `decisions` sahələrini doldurur (hook üsulu, tipoqrafiya, keçid, B-roll, səs, retention); bu fərziyyədir —
`approved_by_user` yalnız istifadəçi təsdiq edəndə (`approve`) true olur və yalnız təsdiqlənmiş qərarlar planlaşdırmada istifadə olunur.

  python -m montaj.refstyle analyze <video> --name <ad> [--sheet-dir qovluq]
  python -m montaj.refstyle decide <ad> --set hook_method="..." --set typography="..."
  python -m montaj.refstyle approve <ad> | list | show <ad>
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

DIR = Path(__file__).resolve().parent / "references"
DECISIONS = ("hook_method", "typography", "transitions", "broll_use", "composition", "sound", "retention", "ad_principles")


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stderr + r.stdout


def probe(src: Path) -> dict[str, Any]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                        "-of", "json", str(src)], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    st, fm = d["streams"][0], d["format"]
    n, dn = st["r_frame_rate"].split("/")
    return {"width": st["width"], "height": st["height"], "fps": round(float(n) / float(dn), 2), "duration": round(float(fm["duration"]), 2)}


def cuts(src: Path, threshold: float = 0.3) -> list[float]:
    out = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-an", "-vf", f"select='gt(scene,{threshold})',metadata=print:file=-", "-f", "null", "-"])
    return sorted({round(float(m), 2) for m in re.findall(r"pts_time:([\d.]+)", out)})


def rhythm(cut_times: list[float], duration: float) -> dict[str, Any]:
    edges = [0.0] + [c for c in cut_times if 0 < c < duration] + [duration]
    shots = [round(b - a, 2) for a, b in zip(edges, edges[1:]) if b - a > 0.05]
    third = max(1.0, duration / 3)
    per_third = [len([c for c in cut_times if i * third <= c < (i + 1) * third]) for i in range(3)]
    return {"cuts": len(cut_times), "shots": len(shots), "avg_shot_s": round(statistics.mean(shots), 2) if shots else duration,
            "median_shot_s": round(statistics.median(shots), 2) if shots else duration, "longest_shot_s": max(shots) if shots else duration,
            "shots_under_1s_pct": round(100 * sum(1 for s in shots if s < 1) / len(shots)) if shots else 0,
            "cuts_in_first_3s": len([c for c in cut_times if c < 3]), "cuts_per_third": per_third,
            "cuts_per_10s": round(len(cut_times) * 10 / duration, 1) if duration else 0}


def audio(src: Path) -> dict[str, Any]:
    out = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-vn", "-af", "ebur128=peak=true,silencedetect=n=-35dB:d=0.4", "-f", "null", "-"])
    tail = out.rsplit("Summary:", 1)[-1]
    li = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", tail)
    lra = re.search(r"LRA:\s+([\d.]+)\s+LU", tail)
    sil = sum(float(x) for x in re.findall(r"silence_duration:\s*([\d.]+)", out))
    return {"loudness_lufs": float(li.group(1)) if li else None, "loudness_range_lu": float(lra.group(1)) if lra else None, "silence_s": round(sil, 1)}


def sheet(src: Path, out: Path, n: int = 12, dur: float = 30) -> Path:
    """Kontakt şəkli (baxış üçün): açılışın ilk kadrları + bərabər aralıqlı kadrlar. Repoya yazılmır."""
    ts = sorted({0.1, 0.6, 1.5} | {dur * (i + 0.5) / (n - 3) for i in range(n - 3)})
    tiles = []
    for i, t in enumerate(ts):
        f = out.with_name(f"{out.stem}_{i}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", "scale=216:-2", str(f)], check=True)
        tiles.append(f)
    ins = sum((["-i", str(f)] for f in tiles), [])
    rows = 2
    per = (len(tiles) + rows - 1) // rows
    flt = "".join(f"[{i}:v]" for i in range(per)) + f"hstack={per}[r0];" + "".join(f"[{i}:v]" for i in range(per, len(tiles))) \
        + f"hstack={len(tiles) - per}[r1];[r0][r1]vstack=2" if len(tiles) - per > 1 else "null"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", flt, "-q:v", "3", str(out)], check=True)
    for f in tiles:
        f.unlink(missing_ok=True)
    return out


def analyze(src: Path, name: str, sheet_dir: Path | None = None) -> dict[str, Any]:
    info = probe(src)
    ct = cuts(src)
    rec = {"name": name, "schema": 1, "source": {"file_name": src.name, **info}, "rhythm": rhythm(ct, info["duration"]), "cut_times": ct, "audio": audio(src),
           "decisions": {k: "" for k in DECISIONS}, "inferred_by_agent": True, "approved_by_user": False,
           "note": "Ölçülər avtomatikdir. `decisions` agentin kontakt şəklinə baxıb çıxardığı FƏRZİYYƏDİR; istifadəçi təsdiq edənə qədər qayda deyil."}
    if sheet_dir:
        sheet_dir.mkdir(parents=True, exist_ok=True)
        rec["sheet"] = str(sheet(src, sheet_dir / f"{name}_sheet.jpg", dur=info["duration"]))
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{name}.json").write_text(json.dumps({k: v for k, v in rec.items() if k != "sheet"}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def load(name: str) -> dict[str, Any]:
    return json.loads((DIR / f"{name}.json").read_text(encoding="utf-8"))


def decide(name: str, kv: dict[str, str]) -> dict[str, Any]:
    rec = load(name)
    bad = [k for k in kv if k not in DECISIONS]
    if bad:
        raise ValueError(f"naməlum sahə: {', '.join(bad)} ({', '.join(DECISIONS)})")
    rec["decisions"].update(kv)
    rec["approved_by_user"] = False  # dəyişən qərar yenidən təsdiq tələb edir
    (DIR / f"{name}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def approve(name: str) -> dict[str, Any]:
    rec = load(name)
    if not any(rec["decisions"].values()):
        raise ValueError("təsdiq üçün `decisions` boşdur — əvvəl `decide` ilə doldur")
    rec["approved_by_user"] = True
    (DIR / f"{name}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def approved_targets() -> list[dict[str, Any]]:
    """Planlaşdırma üçün: YALNIZ istifadəçinin təsdiqlədiyi referansların ritm ölçüləri və qərarları (kopya üçün yox, istiqamət üçün)."""
    out = []
    for f in sorted(DIR.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("approved_by_user"):
            out.append({"name": r["name"], "rhythm": r["rhythm"], "decisions": r["decisions"]})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m montaj.refstyle")
    sub = ap.add_subparsers(dest="cmd", required=True)
    an = sub.add_parser("analyze"); an.add_argument("video"); an.add_argument("--name", required=True); an.add_argument("--sheet-dir")
    de = sub.add_parser("decide"); de.add_argument("name"); de.add_argument("--set", action="append", default=[], metavar="sahə=mətn")
    for c in ("approve", "show"):
        sub.add_parser(c).add_argument("name")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    if a.cmd == "analyze":
        r = analyze(Path(a.video), a.name, Path(a.sheet_dir) if a.sheet_dir else None)
        print(json.dumps({k: r[k] for k in ("rhythm", "audio")}, ensure_ascii=False))
        print("kontakt şəkli:", r.get("sheet", "—"))
        print(f"yazıldı: {DIR / (a.name + '.json')} (video və kadrlar repoya yazılmır)")
    elif a.cmd == "decide":
        print(json.dumps(decide(a.name, dict(x.split("=", 1) for x in a.set))["decisions"], ensure_ascii=False, indent=1))
    elif a.cmd == "approve":
        print("təsdiqləndi:", approve(a.name)["name"])
    elif a.cmd == "show":
        print(json.dumps(load(a.name), ensure_ascii=False, indent=1))
    else:
        for f in sorted(DIR.glob("*.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            print(f"{r['name']:20s} {'təsdiqlənib' if r['approved_by_user'] else 'təsdiqsiz (fərziyyə)'}  orta plan {r['rhythm']['avg_shot_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
