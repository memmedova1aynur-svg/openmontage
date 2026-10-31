"""Qrafika elementlərinin render-i: graphics.js -> şəffaf PNG (Chromium) -> ffmpeg overlay.

Önizləmə ilə eyni: element mərkəzi (x*W, y*H), animasiya formulları graphics.js-dəki animState ilə eynidir:
  k = (t - start)/d,  e = 1-(1-k)^3;  opacity = k;  pop: scale 0.86+0.14e;  slide-up: ty=(1-e)*0.04H;
  slide-left: tx=-(1-e)*0.08W;  çıxış: son dOut saniyədə xətti şəffaflaşma.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from montaj import fonts

TYPES = {"caption", "title", "section", "emphasis", "list", "card"}
DEFAULT_XY = {"caption": (0.5, 0.74), "title": (0.5, 0.14), "section": (0.5, 0.22), "emphasis": (0.5, 0.62),
              "list": (0.5, 0.42), "card": (0.5, 0.42)}  # graphics.js-dəki DEFAULT_XY ilə eyni


def pos(c: dict[str, Any]) -> tuple[float, float]:
    d = DEFAULT_XY.get(c.get("type"), (0.5, 0.5))
    x, y = c.get("x"), c.get("y")
    return (float(d[0] if x is None else x), float(d[1] if y is None else y))
EDITOR = Path(__file__).resolve().parent / "editor"


def is_graphic(c: dict[str, Any]) -> bool:
    return c.get("type") in TYPES


def state_points(c: dict[str, Any]) -> list[float]:
    if c.get("type") == "caption":
        pts = [0.0] + [float(w["s"]) for w in c.get("words") or []]
    elif c.get("type") == "list":
        pts = [0.0] + [float(it.get("at") or 0) for it in c.get("items") or []]
    else:
        pts = [0.0]
    dur = float(c["srcOut"]) - float(c["srcIn"])
    return sorted({round(max(0.0, min(p, dur)), 3) for p in pts})


def rasterize(items: list[tuple[str, dict[str, Any], float]], W: int, H: int, theme: dict[str, Any] | None,
              workdir: Path) -> dict[str, dict[str, Any]]:
    """items: (ad, klip, daxili vaxt). Nəticə: ad -> {file, w, h}."""
    if not items:
        return {}
    fl = [{"family": fam, "weight": w, "path": str(p), "range": fonts.RANGES[sub]}
          for fam, w, sub, p in fonts.editor_font_files()]
    cfg = {"W": W, "H": H, "theme": theme or {}, "fonts": fl,
           "jobs": [{"name": n, "clip": c, "tl": tl + 0.001} for n, c, tl in items]}
    jf = workdir / "raster_jobs.json"
    jf.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    out = workdir / "raster"
    r = subprocess.run(["node", str(EDITOR / "raster.mjs"), str(jf), str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Qrafika rasterizasiyası alınmadı: {r.stderr[-800:]}")
    return json.loads((out / "_result.json").read_text())


def caption_track(caps: list[dict[str, Any]], W: int, H: int, fps: float, total: float, rast: dict[str, Any],
                  workdir: Path) -> Path | None:
    """Bütün altyazı vəziyyətlərini tək şəffaf video trekə yığır (çox overlay əvəzinə bir overlay)."""
    from PIL import Image

    if not caps:
        return None
    blank = workdir / "cap_blank.png"
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    segs: list[tuple[float, float, Path]] = []
    for c in caps:
        pts = state_points(c)
        dur = float(c["srcOut"]) - float(c["srcIn"])
        for k, p in enumerate(pts):
            name = f"{c['id']}__{k}"
            info = rast[name]
            frame = workdir / f"capf_{len(segs)}.png"
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            el = Image.open(info["file"]).convert("RGBA")
            px, py = pos(c)
            x = round(px * W - el.width / 2)
            y = round(py * H - el.height / 2)
            img.alpha_composite(el, (max(0, min(W - el.width, x)), max(0, min(H - el.height, y))))
            img.save(frame)
            a = c["_start"] + p
            b = c["_start"] + (pts[k + 1] if k + 1 < len(pts) else dur)
            segs.append((a, b, frame))
    segs.sort(key=lambda s: s[0])
    lines, t = [], 0.0
    for a, b, f in segs:
        a, b = max(a, t), min(b, total)
        if b <= a:
            continue
        if a - t > 1e-3:
            lines += [f"file '{blank}'", f"duration {a - t:.4f}"]
        lines += [f"file '{f}'", f"duration {b - a:.4f}"]
        t = b
    if total - t > 1e-3:
        lines += [f"file '{blank}'", f"duration {total - t:.4f}"]
    lines.append(f"file '{blank}'")
    lst = workdir / "captions.txt"
    lst.write_text("\n".join(lines))
    out = workdir / "captions.mov"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", f"fps={fps:.4f},format=rgba", "-c:v", "png", "-t", f"{total:.4f}", str(out)],
                   check=True, capture_output=True)
    return out


def overlay_chain(c: dict[str, Any], k: int, n_states: int, a: float, b: float, W: int, H: int, fps_str: str,
                  in_idx: int, cur: str, out: str) -> str:
    """Bir vəziyyət PNG-si üçün filtr: animasiya + overlay. a,b — zaman xəttində intervalı."""
    an = c.get("anim") or {}
    kind = an.get("in", "none") if k == 0 else "none"
    d = max(0.05, float(an.get("d", 0.35)))
    dout = max(0.05, float(an.get("dOut", 0.25)))
    out_fade = (an.get("out", "fade") == "fade") and k == n_states - 1
    dur = b - a
    f = [f"[{in_idx}:v]format=rgba"]
    if kind == "pop":
        f.append(f"scale=w='trunc(iw*(0.86+0.14*(1-pow(1-min(1\\,t/{d:.3f})\\,3)))/2)*2':h=-2:eval=frame")
    if kind != "none":
        f.append(f"fade=t=in:st=0:d={d:.3f}:alpha=1")
    if out_fade and dur > dout:
        f.append(f"fade=t=out:st={dur - dout:.3f}:d={dout:.3f}:alpha=1")
    f.append(f"setpts=PTS+{a:.4f}/TB")
    lab = f"g{in_idx}"
    k3 = f"pow(1-min(1\\,max(0\\,(t-{a:.4f})/{d:.3f}))\\,3)"
    tx = f"-{k3}*{0.08 * W:.2f}" if kind == "slide-left" else "0"
    ty = f"{k3}*{0.04 * H:.2f}" if kind == "slide-up" else "0"
    px, py = pos(c)
    X, Y = px * W, py * H
    return (",".join(f) + f"[{lab}];"
            f"[{cur}][{lab}]overlay=x='{X:.2f}-overlay_w/2+({tx})':y='{Y:.2f}-overlay_h/2+({ty})':"
            f"eval=frame:enable='between(t,{a:.4f},{b:.4f})'[{out}]")
