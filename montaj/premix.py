"""Render-dən əvvəl səs balansı: musiqi və SFX səviyyəsi danışığın ÖLÇÜLMÜŞ səviyyəsinə görə hesablanır.

Problem (Sura sınağı, 2026-11-25): musiqi `volume: 0.12` mütləq dəyər idi. Danışıq yavaş çəkilibsə (−34.7 LUFS) musiqi
(−11.3 LUFS × 0.12 ≈ −29.7 LUFS) danışıqdan ~5 LU yüksək çıxırdı; yekun səsin yenidən tanınması 65% idi. SFX də pikə
çatırdı. Burada səviyyə danışığa nisbətən təyin olunur: musiqi danışıqdan `under` LU aşağı, SFX pik danışıq pikindən
`SFX_UNDER_DB` dB aşağı. Planda `volume`/`vol` rəqəm verilibsə o saxlanılır (istifadəçi qərarı); `"auto"` və ya yoxdursa —
hesablanır. Yekun səviyyəni yenə də render-in loudnorm keçidi (−14 LUFS) təyin edir; burada yalnız NİSBƏT qurulur.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

MUSIC_UNDER_LU = 16.0      # musiqi danışıqdan bu qədər LU aşağı (sınaq: 15 LU-da yenidən tanınma 87%)
SFX_UNDER_DB = 12.0        # SFX pik danışıq pikindən bu qədər dB aşağı (sınaq: 12 dB-də pik −2.0 dBTP)
MIN_GAIN, MAX_GAIN = 0.003, 0.6


def _is_auto(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() == "auto")


def gain(target_db: float, source_db: float) -> float:
    """Xətti əmsal: source səviyyəsini target səviyyəsinə gətirir, [MIN_GAIN, MAX_GAIN] daxilində."""
    return round(min(MAX_GAIN, max(MIN_GAIN, 10 ** ((target_db - source_db) / 20))), 4)


def measure(path: Path, ss: float | None = None, t: float | None = None) -> dict[str, float] | None:
    """EBU R128: {"lufs": inteqral səs, "peak": true peak dBFS}. Səssiz/ölçülməyəndə None (~1 s)."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if ss is not None:
        cmd += ["-ss", f"{ss:.3f}"]
    if t is not None:
        cmd += ["-t", f"{t:.3f}"]
    cmd += ["-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    tail = r.stderr.rsplit("Summary:", 1)[-1]
    i = re.search(r"I:\s+(-?[\d.]+|-inf)\s+LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+|-inf)\s+dBFS", tail)
    if r.returncode != 0 or not i or not p or "inf" in (i.group(1), p.group(1)):
        return None
    return {"lufs": float(i.group(1)), "peak": float(p.group(1))}


def speech_level(project: dict[str, Any], root: Path) -> dict[str, float] | None:
    """Montajda istifadə olunan danışıq hissələrinin (ən yüksək səsli media üzrə) səviyyəsi."""
    from montaj.render import render_plan

    media = {m["id"]: m for m in project.get("media", [])}
    spans: dict[str, list[float]] = {}
    for a in render_plan(project)["audio"]:
        c = a["clip"]
        if a["kind"] != "speech" or c.get("media") not in media:
            continue
        s = spans.setdefault(c["media"], [float(c["srcIn"]), float(c["srcOut"])])
        s[0], s[1] = min(s[0], float(c["srcIn"])), max(s[1], float(c["srcOut"]))
    levels = []
    for mid, (a, b) in spans.items():
        m = measure(root / media[mid]["file"], a, max(0.5, b - a))
        if m:
            levels.append(m)
    if not levels:
        return None
    return {"lufs": max(x["lufs"] for x in levels), "peak": max(x["peak"] for x in levels)}


def resolve(project: dict[str, Any], root: Path, music: list[dict[str, Any]], sfx: list[dict[str, Any]],
            sfx_files: dict[str, Path]) -> dict[str, Any]:
    """Planın `music` və `sfx` siyahılarında `volume`/`vol` "auto" və ya boşdursa danışığa görə doldurur.
    Qayıdır: {"music": [...], "sfx": [...], "report": {...}} (girişlər dəyişdirilmir)."""
    out_m, out_s = [dict(m) for m in music], [dict(s) for s in sfx]
    need_m = [m for m in out_m if _is_auto(m.get("volume"))]
    need_s = [s for s in out_s if _is_auto(s.get("vol"))]
    rep: dict[str, Any] = {"speech": None, "music": [], "sfx": []}
    if not need_m and not need_s:
        return {"music": out_m, "sfx": out_s, "report": rep}
    sp = speech_level(project, root)
    rep["speech"] = sp
    cache: dict[str, dict[str, float] | None] = {}
    for m in need_m:
        under = float(m.get("under", MUSIC_UNDER_LU))
        lv = measure(Path(m["file"])) if sp else None
        if sp and lv:
            m["volume"] = gain(sp["lufs"] - under, lv["lufs"])
            rep["music"].append({"file": Path(m["file"]).name, "volume": m["volume"], "under_lu": under,
                                 "speech_lufs": round(sp["lufs"], 1), "music_lufs": round(lv["lufs"], 1)})
        else:  # ölçülə bilmədi: köhnə standart əvəzinə konservativ
            m["volume"] = 0.05
            rep["music"].append({"file": Path(m["file"]).name, "volume": 0.05, "note": "danışıq/musiqi ölçülmədi"})
    for s in need_s:
        f = sfx_files.get(s.get("kind", ""))
        key = str(f)
        if key not in cache:
            cache[key] = measure(f) if f and f.is_file() else None
        lv = cache[key]
        if sp and lv:
            s["vol"] = gain(sp["peak"] - SFX_UNDER_DB, lv["peak"])
        else:
            s["vol"] = 0.05
        rep["sfx"].append({"kind": s.get("kind"), "vol": s["vol"]})
    return {"music": out_m, "sfx": out_s, "report": rep}


def describe(rep: dict[str, Any]) -> str:
    sp = rep.get("speech")
    if not sp:
        return ""
    bits = [f"danışıq {sp['lufs']:.1f} LUFS (pik {sp['peak']:.1f} dBFS)"]
    for m in rep.get("music") or []:
        bits.append(f"musiqi → {m['volume']} (danışıqdan {m.get('under_lu', '?')} LU aşağı)")
    if rep.get("sfx"):
        bits.append("SFX → " + ", ".join(f"{s['kind']} {s['vol']}" for s in rep["sfx"]))
    return "səs balansı (danışığa görə): " + "; ".join(bits)
