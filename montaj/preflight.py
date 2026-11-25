"""Render-dən əvvəl yoxlama (preflight): tam render (≈2–3 dəq) əvəzinə 360p proksi ilə 3–4 əsas kadr.

Yoxlanan kadrlar: (1) açılış/hook, (2) ən uzun (ən çətin oxunan) altyazı, (3) kartla altyazının birlikdə göründüyü an,
(4) sonluq. Səhvlər bu mərhələdə düzəldilir və layihəyə yazılır:
  * kontur-altyazı (qutusuz) fon üzərində zəif kontrastdadır → qutulu altyazı (brend teması);
  * kart/başlıq Instagram interfeysi zonasına düşür → zonadan çıxana qədər yerdəyişmə (üz örtülməsin);
  * kart başı örtür və ya kartlar üst-üstə düşür → hesabatda (avtomatik düzəliş yoxdur, əl ilə yer dəyiş).
Proksi (HDR→SDR, 360 px) bir dəfə hazırlanır və keşlənir: yenidən preflight ~10 s. Rəng/kəskinlik burada yoxlanmır
(proksi) — yalnız yerləşmə, kontrast, oxunma. Yekun yoxlama `verify`-dir.
"""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

PROXY_W = 360
MIN_CONTRAST = 3.0          # WCAG böyük mətn (altyazı ≥ 20 px bold) üçün
LOW_SHARE = 0.35            # altyazı zonasında kontrastı zəif piksellərin payı
HDR_TO_SDR = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
              "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def _lum(rgb: np.ndarray) -> np.ndarray:
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def contrast(l1: np.ndarray | float, l2: np.ndarray | float) -> np.ndarray | float:
    hi, lo = np.maximum(l1, l2), np.minimum(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _hex(c: str) -> np.ndarray:
    c = (c or "#FFFFFF").split("@")[0].lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def proxy(root: Path, m: dict[str, Any]) -> Path:
    """Medianın 360p SDR proksisi (video yalnız, səssiz); mənbə dəyişməyibsə keşdən."""
    src = root / m["file"]
    key = f"{m['id']}_{src.stat().st_size}_{int(src.stat().st_mtime)}_{PROXY_W}"
    dst = root / "_proxy" / f"{key}.mp4"
    if dst.is_file():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    vf = f"scale={PROXY_W}:-2:flags=fast_bilinear" + ("," + HDR_TO_SDR if m.get("hdr") else ",format=yuv420p")
    tmp = dst.with_suffix(".part.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-an", "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast",
                    "-crf", "27", "-g", "15", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(dst)
    return dst


def lowres_project(project: dict[str, Any], root: Path) -> dict[str, Any]:
    """Proksi mediası ilə yüngül layihə nüsxəsi: yalnız video və mətn/qrafika (səs yoxdur)."""
    from montaj.render import track_kinds

    q = copy.deepcopy(project)
    kinds = track_kinds(q)
    q["clips"] = [c for c in q["clips"] if kinds[c["track"]] not in ("speech", "music", "sfx", "voice", "audio")]
    q["background"], q["fxRender"] = {}, {}
    used = {c.get("media") for c in q["clips"] if kinds[c["track"]] in ("video", "overlay")}
    for m in q["media"]:
        if m["id"] in used and m.get("hasVideo") and not m.get("isImage"):
            p = proxy(root, m)
            ratio = m["height"] / m["width"] if m.get("width") else 16 / 9
            m.update(file=str(p.relative_to(root)), hdr=False, width=PROXY_W, height=int(round(PROXY_W * ratio / 2) * 2))
    ratio = project["height"] / project["width"]
    q["width"], q["height"] = PROXY_W, int(round(PROXY_W * ratio / 2) * 2)
    q["loudnessTarget"] = None
    return q


def moments(project: dict[str, Any]) -> list[dict[str, Any]]:
    """3–4 əsas an: hook, ən uzun altyazı, kart+altyazı, sonluq."""
    from montaj.render import render_plan

    pl = render_plan(project)
    total = pl["main"]
    caps = [t for t in pl["text"] if t["clip"].get("autoSub") or str(t["clip"].get("id", "")).startswith("sub_")]
    gfx = [t for t in pl["text"] if t["clip"].get("type") in ("title", "emphasis", "section", "badge", "list", "card", "offer", "cta", "lower", "choice", "type", "note", "block", "bars")]
    out: list[dict[str, Any]] = []
    hook = next((g for g in sorted(gfx, key=lambda g: g["start"]) if g["start"] < 10), None)
    out.append({"label": "açılış", "t": round(hook["start"] + min(0.8, (hook["end"] - hook["start"]) / 2), 2) if hook else 0.8,
                **({"gfx": hook["clip"]} if hook else {})})
    if caps:
        c = max(caps, key=lambda t: len(str(t["clip"].get("text") or "")))
        out.append({"label": "ən uzun altyazı", "t": round((c["start"] + c["end"]) / 2, 2), "caption": c["clip"]})
    both = next((g for g in sorted(gfx, key=lambda g: g["start"]) if g is not hook
                 and any(c["start"] < g["end"] and c["end"] > g["start"] for c in caps)), None)
    if both:
        out.append({"label": f"{both['clip'].get('type')} + altyazı", "t": round(both["start"] + min(1.0, (both["end"] - both["start"]) / 2), 2)})
    last_g = max(gfx, key=lambda g: g["end"], default=None)
    if last_g and last_g["start"] > total - 8:
        out.append({"label": "sonluq", "t": round(min(total - 0.3, last_g["start"] + 0.8), 2)})
    else:
        out.append({"label": "sonluq", "t": round(max(0.5, total - 1.0), 2)})
    seen, uniq = set(), []
    for m in out:
        k = round(m["t"], 1)
        if k not in seen:
            seen.add(k)
            uniq.append(m)
    return uniq[:4]


def caption_contrast(frame: np.ndarray, clip: dict[str, Any], y: float = 0.74) -> dict[str, Any]:
    """Altyazının mətn rəngi ilə fon kontrastı. Qutulu altyazı: mətn ↔ qutu (qutunun fon üzərində qarışığı);
    qutusuz: mətn ↔ altyazı zonasındakı fon pikselləri (mətnin öz rəngindəki pikseller çıxarılır)."""
    H, W = frame.shape[:2]
    band = frame[int(H * (y - 0.045)): int(H * (y + 0.045)), int(W * 0.08): int(W * 0.92)].astype(np.float32)
    tcol = _hex(clip.get("color") or "#FFFFFF")
    acol = _hex(clip.get("activeColor") or clip.get("color") or "#FFFFFF")
    bg = str(clip.get("bg") or "none")
    if bg != "none":
        alpha = float(bg.split("@")[1]) if "@" in bg else 1.0
        rows = band.reshape(-1, 3)
        base = np.median(rows, axis=0)
        box = _hex(bg) * alpha + base * (1 - alpha)
        c = float(min(contrast(_lum(tcol), _lum(box)), contrast(_lum(acol), _lum(box))))
        return {"mode": "box", "ratio": round(c, 2), "ok": c >= 4.5 or c >= MIN_CONTRAST}
    pix = band.reshape(-1, 3)
    far = np.linalg.norm(pix - tcol, axis=1) > 60  # mətnin öz rəngi fon deyil
    far &= np.linalg.norm(pix - acol, axis=1) > 60
    pix = pix[far] if far.sum() > 50 else pix
    ratios = contrast(_lum(tcol), _lum(pix))
    low = float((ratios < MIN_CONTRAST).mean())
    return {"mode": "stroke", "ratio": round(float(np.median(ratios)), 2), "low_share": round(low, 2), "ok": low <= LOW_SHARE}


def _fix_captions_to_box(q: dict[str, Any]) -> dict[str, Any]:
    from montaj.session import node_tl

    th = (q.get("brand") or {}).get("theme") or {}
    st = dict(q["subtitles"].get("style") or {})
    st["bg"] = f"{th.get('primary', '#333333')}@0.85"
    if th.get("text"):
        st["color"] = th["text"]
    return node_tl("setSubtitleStyle", q, st)


_ZONE_DY = {"yuxarı": 0.02, "aşağı": -0.02}


MIN_SEG = 2.0   # element (B-roll/animasiya) və aralarındakı ekspert hissəsi ən azı ~2 s


def check_segments(project: dict[str, Any]) -> list[str]:
    """Çox qısa element/ekspert hissələri (0.1–1 s) və sıçrayışlı punch-in — xəbərdarlıq (avtomatik düzəliş yoxdur)."""
    from montaj.render import render_plan

    pl = render_plan(project)
    out: list[str] = []
    spans: list[tuple[float, float, str]] = []
    for o in pl["overlay"]:
        if o["clip"].get("mode") != "pip":
            spans.append((o["start"], o["start"] + o["dur"], "overlay"))
    for v in pl["video"]:
        if v["clip"].get("broll"):
            spans.append((v["start"], v["start"] + v["dur"], "insert"))
    spans.sort()
    for a, b, k in spans:
        if b - a < MIN_SEG - 1e-6:
            out.append(f"{a:.1f} s: element yalnız {b - a:.1f} s göstərilir (≥{MIN_SEG:.0f} s olmalıdır)")
    for (a1, b1, _), (a2, _b2, _k2) in zip(spans, spans[1:]):
        if 0 < a2 - b1 < MIN_SEG - 1e-6:
            out.append(f"{b1:.1f} s: elementlər arasında ekspert yalnız {a2 - b1:.1f} s görünür (≥{MIN_SEG:.0f} s olmalıdır)")
    if any((c.get("frame") or {}).get("planZoom") for c in project["clips"]):
        out.append("punch-in (`zooms`) sıçrayışlıdır — hamar zoom üçün `multicam` calm istifadə et")
    return out


def _has_veil(q: dict[str, Any], g: dict[str, Any]) -> bool:
    s0, s1 = float(g.get("start", 0)), float(g.get("start", 0)) + float(g["srcOut"]) - float(g["srcIn"])
    return any(c.get("type") == "veil" and float(c.get("start", 0)) <= s0 + 0.05 and float(c.get("start", 0)) + float(c["srcOut"]) - float(c["srcIn"]) >= s1 - 0.05
               for c in q["clips"])


def add_veils(q: dict[str, Any], a: float = 0.42) -> tuple[dict[str, Any], int]:
    """Kartsız yazı elementlərinin hər biri üçün (altında) yumşaq üst qradiyent klipi əlavə edir."""
    from montaj.session import node_tl

    n = 0
    for c in [x for x in q["clips"] if x.get("type") in ("type", "note") and not _has_veil(q, x)]:
        dur = float(c["srcOut"]) - float(c["srcIn"])
        vid = f"veil_{c['id']}"
        q = node_tl("addGraphic", q, {"id": vid, "type": "veil", "start": c["start"], "dur": dur, "y": 0.21, "h": 0.42, "a": a, "bleed": True, "origin": "plan",
                                      "anim": {"in": "fade", "d": 0.5, "out": "fade", "dOut": 0.4}})
        v = next(x for x in q["clips"] if x["id"] == vid)
        q["clips"] = [x for x in q["clips"] if x["id"] != vid]
        q["clips"].insert(next(i for i, x in enumerate(q["clips"]) if x["id"] == c["id"]), v)  # yazının ALTINDA (əvvəl çəkilir)
        n += 1
    return q, n


def fix_layout(q: dict[str, Any], root: Path, workdir: Path, tries: int = 3) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    """layout_check səhvləri: zonaya düşən kart/başlıq y-ni 0.02 addımla zonadan çıxarır (üz örtülməsə).
    Qayıdır: (layihə, edilən düzəlişlər, qalan problemlər)."""
    from montaj import quality

    notes: list[str] = []
    probs: list[dict[str, Any]] = []
    for _ in range(tries):
        probs = quality.layout_check(q, root, workdir)
        zone = [p for p in probs if p.get("id") and p.get("zone") in _ZONE_DY and not str(p["id"]).startswith("sub_")]
        if not zone:
            break
        p = zone[0]
        c = next((x for x in q["clips"] if x["id"] == p["id"]), None)
        if not c:
            break
        from montaj.graphics import pos

        y0 = pos(c)[1]
        box = p.get("box") or [0, 0, 1, 1]
        # bir addımda zonadan çıxar: yuxarı zona y<0.08, aşağı zona y>0.86 (+0.01 ehtiyat)
        dy = (0.09 - box[1]) if p["zone"] == "yuxarı" else (0.85 - box[3])
        c["y"] = round(y0 + (dy if abs(dy) > 0.005 else _ZONE_DY[p["zone"]]), 3)
        notes.append(f"{c.get('type')} “{str(c.get('text') or '')[:24]}”: y {y0:.3f} → {c['y']:.3f} (interfeys zonası: {p['zone']})")
    return q, notes, probs


def run(pid: str) -> dict[str, Any]:
    """Preflight: düzəlişlər layihəyə yazılır. Qayıdır hesabat (kadrlar `out/<pid>/preflight.jpg`)."""
    from montaj import store
    from montaj.render import render
    from montaj.session import out_dir

    t0 = time.time()
    p = store.load(pid)
    root = store.project_dir(pid)
    rep: dict[str, Any] = {"fixes": [], "problems": [], "moments": []}
    with tempfile.TemporaryDirectory(prefix="pf_") as tmp:
        q, notes, left = fix_layout(copy.deepcopy(p), root, Path(tmp) / "lay")
        rep["fixes"] += notes
        rep["problems"] += check_segments(q)
        rep["problems"] += [f"{x['t']:.1f} s {x['what']}" for x in left]
        lo = lowres_project(q, root)
        mp4 = Path(tmp) / "pf.mp4"
        render(lo, root, mp4, lambda x: None)
        mm = moments(q)
        frames = []
        for m in mm:
            f = Path(tmp) / f"f_{len(frames)}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{m['t']:.2f}", "-i", str(mp4), "-frames:v", "1", str(f)], check=True)
            frames.append(f)
        from PIL import Image

        bad, fixed_box = False, None
        for m, f in zip(mm, frames):
            info = {"label": m["label"], "t": m["t"]}
            if m.get("caption") and q.get("subtitles", {}).get("enabled", True):
                img = np.asarray(Image.open(f).convert("RGB"))
                cc = caption_contrast(img, m["caption"])
                info["caption_contrast"] = cc
                if not cc["ok"]:
                    bad = True
                    th = (q.get("brand") or {}).get("theme") or {}
                    boxed = {**m["caption"], "bg": f"{th.get('primary', '#333333')}@0.85", "color": th.get("text") or m["caption"].get("color")}
                    fixed_box = caption_contrast(img, boxed)  # düzəlişdən sonrakı kontrast (eyni fon, yenidən render yoxdur)
                    info["caption_contrast_after_fix"] = fixed_box
            rep["moments"].append(info)
        # kartsız (birbaşa video üzərində) yazılar: fon açıq/qarışıqdırsa oxunmur → çox yumşaq tünd üst qradiyent (veil), ləkə yox
        from montaj.graphics import pos as _pos

        for m, f in zip(mm, frames):
            g = m.get("gfx")
            if g and g.get("type") in ("type", "note") and not _has_veil(q, g):
                cc = caption_contrast(np.asarray(Image.open(f).convert("RGB")), {"color": g.get("color") or "#FFFFFF", "bg": "none"}, y=_pos(g)[1])
                for info in rep["moments"]:
                    if info["label"] == m["label"] and info["t"] == m["t"]:
                        info["text_contrast"] = cc
                if not cc["ok"]:
                    q, n = add_veils(q)
                    rep["fixes"].append(f"birbaşa video üzərindəki yazı oxunmur (kontrast {cc['ratio']}): {n} yazıya yumşaq üst qradiyent (veil) əlavə olundu")
                    break
        if bad:
            q = _fix_captions_to_box(q)
            rep["fixes"].append("altyazı: kontur → qutulu (fon üzərində kontrast zəif idi); kadr şəkli düzəlişdən əvvəlkidir")
            if fixed_box and not fixed_box["ok"]:
                rep["problems"].append("altyazı kontrastı düzəlişdən sonra da zəifdir — rəngi əl ilə yoxla")
        sheet = out_dir(pid) / "preflight.jpg"
        ins = sum((["-i", str(f)] for f in frames), [])
        subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", f"hstack={len(frames)}" if len(frames) > 1 else "null",
                        "-q:v", "3", str(sheet)], check=True)
        rep["sheet"] = str(sheet)
    if rep["fixes"]:
        p2 = store.load(pid)
        q["revision"] = p2["revision"]
        store.save(pid, q, p2["revision"])
    rep["seconds"] = round(time.time() - t0, 1)
    (out_dir(pid) / "preflight.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return rep


def describe(rep: dict[str, Any]) -> list[str]:
    out = [f"preflight: {len(rep['moments'])} kadr, {rep['seconds']} s → {rep.get('sheet')}"]
    for m in rep["moments"]:
        cc = m.get("caption_contrast")
        af = m.get("caption_contrast_after_fix")
        extra = f" — altyazı kontrastı {cc['ratio']} ({cc['mode']}{', zəif' if not cc['ok'] else ''})" if cc else ""
        extra += f" → düzəlişdən sonra {af['ratio']} ({af['mode']})" if af else ""
        tc = m.get("text_contrast")
        extra += f" — yazı kontrastı {tc['ratio']}{', zəif' if not tc['ok'] else ''}" if tc else ""
        out.append(f"  {m['t']:5.1f} s {m['label']}{extra}")
    out += [f"  düzəldildi: {x}" for x in rep["fixes"]]
    out += [f"  ! {x}" for x in rep["problems"]]
    return out
