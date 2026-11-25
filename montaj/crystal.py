"""Adaptive Crystal Clear Natural Look — bütün müştərilər üçün ortaq adaptiv görüntü optimallaşdırması.

Vizual referans: təsdiqlənmiş V3 (montaj/references/crystal_clear_v3/). Parametrlər mexaniki tətbiq OLUNMUR:
hər videonun təmsilçi kadrları analiz edilir, yalnız ehtiyac olan parametrlər V3 səviyyəsinə qədər tənzimlənir.
Yaxşı vəziyyətdə olan parametrə toxunulmur; hər şey qaydasındadırsa korreksiya yoxdur ("asis").

Axın:  prepare(src) = analyze → decide → nümunə kadrlarda yoxlama (+ lazım olsa düzəliş) → keş
       filters(params) → ffmpeg zənciri (yalnız zəif luma kəskinliyi, mikro-kontrast, yüngül xroma təmizləmə, zəif canlılıq, zəif şəffaflıq)
       temporal_check(src, out) → yekun render yoxlaması (kadrlar arası rəng/işıq sıçrayışı, rəng sürüşməsi)

Məhdudiyyətlər (açıq): hədlər Xəyyam Həsənovun 3 fərqli çəkiliş mühitindən kalibrlənib; ilk istifadədə yeni müştəridə
nəticə nümunə kadrla yoxlanılmalıdır. HDR mənbədə avtomatik korreksiya edilmir. Upscaling və AI emalı yoxdur.

CLI:  python -m montaj.crystal analyze <video> [--json]
      python -m montaj.crystal sample <video> --start 20 --dur 8 --out nümunə.mp4   (hərəkətli nümunə + hərəkət yoxlaması)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

# ── V3 referansı: təsdiqlənmiş kadrda (Xəyyam, video 05, 20 s) istifadə olunan REAL parametrlər ─────────────────────────
V3_PARAMS: dict[str, float] = {
    "luma_denoise": 0.4,     # hqdn3d luma_spatial
    "chroma_denoise": 1.6,   # hqdn3d chroma_spatial (rəng səs-küyü; dəri/saqqal teksturasına toxunmur)
    "micro": 0.09,           # unsharp 13x13, yalnız parlaqlıq — mikro-kontrast
    "sharpen": 0.14,         # unsharp 5x5, yalnız parlaqlıq — incə kəskinlik
    "lift": 1.0,             # curves master 0/0 0.25/0.256 0.6/0.614 1/1 (≈ +2/255) — şəffaflıq/parlaqlıq
    "vibrance": 0.012,       # vibrance filtri
}
# V3 kadrının ölçülmüş "barmaq izi" (adaptiv hədlərin ankeri): orta parlaqlıq, kəskinlik, səs-küy, doyma
REF = {"mean_luma": 118.0, "sharp": None, "noise": None, "sat": None}  # sharp/noise/sat — ilk kalibrləmədə dolur (REF_FILE)
REF_FILE = Path(__file__).parent / "references" / "crystal_clear_v3" / "params.json"

# Qoruyucu hədlər (nümunə kadr yoxlaması): bunlardan kənara çıxırsa müvafiq parametr azaldılır
LIMITS = {"black_pt": 3.0, "white_pt": 4.0, "luma_shift": 6.0, "skin_rg": 0.025, "neutral_cast": 0.015, "sat_rel": 0.12, "clip_pp": 0.5, "sharp_ratio": 1.4, "noise_ratio": 3.2}  # noise_ratio: V3 özü ölçülən yüksək tezliyi 2.3× artırır (kəskinlik təsiri) → hədd V3×1.4
GOOD = {"sharp_factor": 1.6, "sat_hi": 0.40, "sat_lo": 0.07, "noise_quiet": 0.45, "mid_target": 135.0, "wb_tol": 0.06}


# ── kadr alma və ölçmə ───────────────────────────────────────────────────────────────────────────────────────────────────
def _run(a: list[str], **k: Any) -> subprocess.CompletedProcess:
    return subprocess.run(a, check=True, capture_output=True, **k)


def probe(src: Path | str) -> dict[str, Any]:
    r = json.loads(_run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height,color_transfer,r_frame_rate:format=duration", "-of", "json", str(src)]).stdout)
    s = r["streams"][0]
    return {"w": s["width"], "h": s["height"], "dur": float(r["format"]["duration"]), "hdr": s.get("color_transfer") in ("smpte2084", "arib-std-b67")}


def grab(src: Path | str, t: float, width: int = 1080, p: dict[str, Any] | None = None) -> np.ndarray:
    p = p or probe(src)
    w = min(width, p["w"]); h = int(round(p["h"] * w / p["w"] / 2) * 2)
    raw = _run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-vf", f"scale={w}:{h}:flags=lanczos",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def _luma(a: np.ndarray) -> np.ndarray:
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def _box3(y: np.ndarray) -> np.ndarray:
    p = np.pad(y, 1, mode="edge")
    return sum(p[i:i + y.shape[0], j:j + y.shape[1]] for i in range(3) for j in range(3)) / 9.0


def _masks(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = frame.astype(np.float32); y = _luma(a); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    cb = 128 - 0.1687 * r - 0.3313 * g + 0.5 * b; cr = 128 + 0.5 * r - 0.4187 * g - 0.0813 * b
    skin = (cb > 77) & (cb < 127) & (cr > 133) & (cr < 173) & (y > 40) & (y < 230)
    neutral = (y > 140) & ((a.max(-1) - a.min(-1)) < 25)
    return skin, neutral


def measure(frame: np.ndarray, like: np.ndarray | None = None) -> dict[str, float]:
    """Bir kadrın ölçüləri (RGB uint8). `like` — dəri/neytral piksel maskaları həmin (orijinal) kadrdan götürülür:
    korreksiyadan əvvəl/sonra eyni piksellər müqayisə olunsun (maska özü parlaqlıqla dəyişib saxta rəng sürüşməsi göstərməsin)."""
    a = frame.astype(np.float32)
    y = _luma(a)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    cb = 128 - 0.1687 * r - 0.3313 * g + 0.5 * b
    skin, neutral = _masks(frame if like is None else like)
    m: dict[str, float] = {"mean_luma": float(y.mean()), "p1": float(np.percentile(y, 1)), "p50": float(np.percentile(y, 50)),
                           "p99": float(np.percentile(y, 99)), "clip_hi": float((y >= 250).mean() * 100), "clip_lo": float((y <= 5).mean() * 100)}
    m["skin_frac"] = float(skin.mean())
    if skin.mean() > 0.004:
        m["skin_luma"] = float(y[skin].mean()); m["skin_rg"] = float(r[skin].mean() / max(g[skin].mean(), 1))
    if neutral.mean() > 0.005:
        m["cast_rg"] = float(r[neutral].mean() / max(g[neutral].mean(), 1)); m["cast_bg"] = float(b[neutral].mean() / max(g[neutral].mean(), 1))
    mid = (y > 30) & (y < 230) & ~skin
    m["sat"] = float(sat[mid].mean()) if mid.any() else 0.0
    # kəskinlik: qradiyent enerjisinin (yüksək tezlik) orta tezliyə nisbəti; səs-küy: ən hamar bloklarda qalıq dispersiya
    gx = np.abs(np.diff(y, axis=1))[:-1]; gy = np.abs(np.diff(y, axis=0))[:, :-1]
    grad = gx + gy
    m["sharp"] = float(np.percentile(grad, 99) / max(np.percentile(grad, 75), 0.5))
    res = y - _box3(y)
    bs = 16; H, W = (y.shape[0] // bs) * bs, (y.shape[1] // bs) * bs
    rb = res[:H, :W].reshape(H // bs, bs, W // bs, bs).swapaxes(1, 2).reshape(-1, bs * bs)
    yb = y[:H, :W].reshape(H // bs, bs, W // bs, bs).swapaxes(1, 2).reshape(-1, bs * bs)
    flat = np.argsort(yb.std(1))[: max(8, len(yb) // 6)]  # ən hamar 1/6 blok
    m["noise"] = float(np.sqrt(np.median(rb[flat].var(1))) * 1.5)
    cbr = (cb - _box3(cb))[:H, :W].reshape(H // bs, bs, W // bs, bs).swapaxes(1, 2).reshape(-1, bs * bs)
    m["chroma_noise"] = float(np.sqrt(np.median(cbr[flat].var(1))) * 1.5)
    return m


def analyze(src: Path | str, n: int = 5) -> dict[str, Any]:
    """Təmsilçi kadrlar (10–90% aralığında bərabər) → orta ölçülər. Qısa, bir dəfəlik."""
    p = probe(src)
    ts = [p["dur"] * (0.1 + 0.8 * k / max(n - 1, 1)) for k in range(n)] if p["dur"] > 1 else [0.0]
    frames = [grab(src, t, p=p) for t in ts]
    ms = [measure(f) for f in frames]
    keys = set().union(*[m.keys() for m in ms])
    out = {k: float(np.mean([m[k] for m in ms if k in m])) for k in keys}
    out["jitter_luma"] = float(np.std([m["mean_luma"] for m in ms]))
    out["probe"] = p; out["times"] = [round(t, 2) for t in ts]
    return out


# ── qərar: yalnız ehtiyac olan parametrlər ───────────────────────────────────────────────────────────────────────────────
def _ref() -> dict[str, float]:
    if REF_FILE.exists():
        j = json.loads(REF_FILE.read_text())
        return {**REF, **{k: v for k, v in j.get("reference_metrics", {}).items() if v is not None}}
    return REF


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def decide(m: dict[str, Any]) -> dict[str, Any]:
    """Ölçülərdən parametrlər. Hər parametr: yaxşıdırsa 0; pisdirsə V3 səviyyəsinə doğru (həddi 1.6×V3)."""
    ref = _ref(); P = {k: 0.0 for k in V3_PARAMS}; notes: list[str] = []
    if m.get("probe", {}).get("hdr"):
        return {"mode": "skip", "params": P, "notes": ["HDR mənbə: avtomatik korreksiya yoxdur (əvvəl tone-map)"], "metrics": _pub(m)}
    # kəskinlik / mikro-kontrast
    if ref.get("sharp"):
        good = ref["sharp"] * GOOD["sharp_factor"]
        f = _clip((good - m["sharp"]) / max(good - ref["sharp"], 1e-6), 0, 1.6)
    else:
        f = 1.0
    P["sharpen"] = round(V3_PARAMS["sharpen"] * f, 3); P["micro"] = round(V3_PARAMS["micro"] * f, 3)
    notes.append(f"kəskinlik ×{f:.2f}" + (" (kifayət qədər kəskindir — toxunulmur)" if f == 0 else ""))
    # səs-küy: sakitdirsə təmizləmə yoxdur
    if ref.get("noise"):
        nf = 0.0 if m["noise"] < GOOD["noise_quiet"] else _clip(m["noise"] / ref["noise"], 0, 2.5)
        cf = 0.0 if m["chroma_noise"] < 0.15 else nf  # xroma ölçüsü kadrdan-kadra tərəddüd edir: yalnız "səs-küy var/yoxdur" üçün; miqdar luma ilə
    else:
        nf = cf = 1.0
    P["luma_denoise"] = round(min(1.2, V3_PARAMS["luma_denoise"] * nf), 2); P["chroma_denoise"] = round(min(4.0, V3_PARAMS["chroma_denoise"] * cf), 2)
    notes.append(f"səs-küy luma {m['noise']:.2f} / xroma {m['chroma_noise']:.2f}")
    # şəffaflıq: işıq balanslıdırsa yox; qaranlıq/solğundursa V3 səviyyəsinə qədər
    mid = _clip((GOOD["mid_target"] - m["mean_luma"]) / max(GOOD["mid_target"] - ref["mean_luma"], 1), 0, 1.6)
    if "skin_luma" in m and m.get("skin_frac", 0) > 0.01:
        mid = max(mid, _clip((115 - m["skin_luma"]) / 25, 0, 1.6))  # üz tünddürsə daha çox
        if m["skin_luma"] > 170: mid = 0.0
    if m["clip_hi"] > 2.0: mid = 0.0  # yanmış ağlar — işıq artırılmır
    P["lift"] = round(mid, 2); notes.append(f"işıq ×{mid:.2f} (orta {m['mean_luma']:.0f})")
    # canlılıq: artıq doymuşdursa yox; solğundursa çox cüzi artır
    if m["sat"] >= GOOD["sat_hi"]: v = 0.0
    elif m["sat"] <= GOOD["sat_lo"]: v = V3_PARAMS["vibrance"] * 2
    else: v = V3_PARAMS["vibrance"]
    P["vibrance"] = round(v, 3); notes.append(f"canlılıq {m['sat']:.2f}")
    # ağ balansı: yalnız aydın şəkildə pozulubsa (V3 balansa toxunmur); diqqət — bu istiqamətdə avtomatik dəyişiklik edilmir, yalnız xəbərdarlıq
    if "cast_bg" in m and abs(m["cast_bg"] - 1) > GOOD["wb_tol"] or "cast_rg" in m and abs(m["cast_rg"] - 1) > GOOD["wb_tol"]:
        notes.append(f"! ağ balansı çəkilişdə pozulub (R/G {m.get('cast_rg', 0):.2f}, B/G {m.get('cast_bg', 0):.2f}) — avtomatik düzəliş yoxdur, əl ilə baxın")
    mode = "asis" if all(v == 0 for v in P.values()) else ("minimal" if max(P["sharpen"] / V3_PARAMS["sharpen"], P["lift"], 0) <= 1.1 else "adaptive")
    return {"mode": mode, "params": P, "notes": notes, "metrics": _pub(m)}


def _pub(m: dict[str, Any]) -> dict[str, float]:
    return {k: round(v, 3) for k, v in m.items() if isinstance(v, (int, float))}


# ── ffmpeg zənciri (V3 ilə eyni quruluş) ──────────────────────────────────────────────────────────────────────────────────
def filters(P: dict[str, float], video: bool = True) -> list[str]:
    f: list[str] = []
    if P.get("luma_denoise", 0) > 0.01 or P.get("chroma_denoise", 0) > 0.01:
        tmp = (3, 4) if video and P.get("luma_denoise", 0) > 0.9 else (0, 0)  # temporal yalnız səs-küy aydın yüksək olanda
        f.append(f"hqdn3d=luma_spatial={P.get('luma_denoise', 0):.2f}:chroma_spatial={P.get('chroma_denoise', 0):.2f}:luma_tmp={tmp[0]}:chroma_tmp={tmp[1]}")
    if P.get("micro", 0) > 0.005: f.append(f"unsharp=13:13:{P['micro']:.3f}:13:13:0")
    if P.get("sharpen", 0) > 0.005: f.append(f"unsharp=5:5:{P['sharpen']:.3f}:5:5:0")
    lf = P.get("lift", 0)
    if lf > 0.01: f.append(f"curves=master='0/0 0.25/{0.25 + 0.006 * lf:.4f} 0.6/{0.6 + 0.014 * lf:.4f} 1/1'")
    if P.get("vibrance", 0) > 0.002: f.append(f"vibrance=intensity={P['vibrance']:.3f}")
    return f


def chain(P: dict[str, float], video: bool = True) -> str:
    return ",".join(filters(P, video)) or "null"


def _apply(frame: np.ndarray, P: dict[str, float]) -> np.ndarray:
    h, w, _ = frame.shape
    raw = _run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-i", "-", "-vf", chain(P, video=False), "-frames:v", "1",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], input=frame.tobytes()).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


# ── nümunə kadrlarda yoxlama; yalnız problem varsa müvafiq parametr azalır ────────────────────────────────────────────────
def check(before: dict[str, float], after: dict[str, float]) -> list[str]:
    pr: list[str] = []
    if abs(after["mean_luma"] - before["mean_luma"]) > LIMITS["luma_shift"]: pr.append("lift")
    if "skin_rg" in before and "skin_rg" in after and abs(after["skin_rg"] / before["skin_rg"] - 1) > LIMITS["skin_rg"]: pr += ["vibrance", "lift"]
    if "cast_bg" in before and "cast_bg" in after and abs(after["cast_bg"] - before["cast_bg"]) > LIMITS["neutral_cast"]: pr += ["vibrance", "lift"]
    if before["sat"] > 0 and abs(after["sat"] / before["sat"] - 1) > LIMITS["sat_rel"]: pr.append("vibrance")
    if after["clip_hi"] - before["clip_hi"] > LIMITS["clip_pp"]: pr += ["lift", "micro"]
    if after["p1"] - before["p1"] > LIMITS["black_pt"]: pr.append("lift")      # qara qara qalsın (süd-bulanıq qara yoxdur)
    if before["p99"] - after["p99"] > LIMITS["white_pt"]: pr.append("lift")    # ağ ağ qalsın (solğun ağ yoxdur)
    if after["sharp"] / max(before["sharp"], 1e-6) > LIMITS["sharp_ratio"]: pr += ["sharpen", "micro"]
    if after["noise"] / max(before["noise"], 1e-6) > LIMITS["noise_ratio"]: pr += ["sharpen", "micro"]
    return sorted(set(pr))


def prepare(src: Path | str, n: int = 5, cache: bool = True) -> dict[str, Any]:
    """analyze → decide → nümunə yoxlama (maks. 2 düzəliş dövrü) → keş. Nəticə: {"params", "mode", "notes", "source"}."""
    m = analyze(src, n); d = decide(m)
    if d["mode"] in ("skip", "asis"):
        return {**d, "source": "analysis", "fixes": []}
    sig = _signature(m)
    hit = _cache_get(sig) if cache else None
    P = dict(hit["params"]) if hit else dict(d["params"]); src_kind = "cache" if hit else "analysis"
    frames = [grab(src, t) for t in m["times"][:3]]
    befores = [measure(f) for f in frames]; fixes: list[str] = []
    for _ in range(3):
        problems = sorted({p for f, b in zip(frames, befores) for p in check(b, measure(_apply(f, P), like=f))})
        if not problems: break
        for p in problems: P[p] = round(P.get(p, 0) * 0.5, 3)
        fixes.append("azaldıldı: " + ", ".join(problems))
        if src_kind == "cache": src_kind = "cache+düzəliş"
    else:
        P = {k: 0.0 for k in P}; fixes.append("yoxlama keçmədi — korreksiya söndürüldü")
    out = {**d, "params": P, "source": src_kind, "fixes": fixes}
    if cache and not hit and not fixes: _cache_put(sig, P)
    return out


# ── keş: eyni işıq və məkan üçün təkrar istifadə (hər dəfə yenə də yoxlanır) ─────────────────────────────────────────────
def _signature(m: dict[str, Any]) -> list[float]:
    return [m["mean_luma"] / 255, m.get("cast_bg", 1.0), m.get("cast_rg", 1.0), m["sat"], m.get("skin_rg", 1.5) / 2]


def _cache_file() -> Path:
    from montaj.config import data_dir
    return data_dir() / "crystal_cache.json"


def _cache_get(sig: list[float]) -> dict[str, Any] | None:
    try:
        items = json.loads(_cache_file().read_text())
    except Exception:
        return None
    best = min(items, key=lambda e: sum(abs(a - b) for a, b in zip(e["sig"], sig)), default=None)
    return best if best and sum(abs(a - b) for a, b in zip(best["sig"], sig)) < 0.06 else None


def _cache_put(sig: list[float], P: dict[str, float]) -> None:
    f = _cache_file()
    try:
        items = json.loads(f.read_text())
    except Exception:
        items = []
    items.append({"sig": sig, "params": P, "id": hashlib.sha1(json.dumps(sig).encode()).hexdigest()[:8]})
    f.write_text(json.dumps(items[-50:], indent=1))


def chain_for(src: Path | str, override: str | None = None) -> str:
    """Montaj skriptləri üçün: verilmiş əl ilə `color` zənciri varsa onu, yoxsa adaptiv Crystal Clear zəncirini qaytarır."""
    if override:
        return override
    r = prepare(src)
    warn = [n for n in r["notes"] if n.startswith("!")] + (["! KORREKSİYA YOXDUR (" + "; ".join(r["notes"]) + ")"] if r["mode"] == "skip" else [])
    for w in warn + r["fixes"]:
        print("XƏBƏRDARLIQ [crystal]:", w, file=sys.stderr)
    return chain(r["params"])


# ── hərəkətdə / yekun yoxlama ─────────────────────────────────────────────────────────────────────────────────────────────
def _frames(path: Path | str, ss: float, t: float, fps: float, w: int = 540) -> list[np.ndarray]:
    p = probe(path); h = int(round(p["h"] * w / p["w"] / 2) * 2)
    raw = _run(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", str(path), "-vf", f"fps={fps},scale={w}:{h}:flags=lanczos",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]).stdout
    a = np.frombuffer(raw, np.uint8); k = len(a) // (w * h * 3)
    return list(a[: k * w * h * 3].reshape(k, h, w, 3))


def temporal_check(src: Path | str, out: Path | str, ss: float = 0.0, t: float | None = None, fps: float = 4.0) -> dict[str, Any]:
    """Orijinal ilə nəticə arasında kadr-kadr müqayisə: işıq/rəng sürüşməsi sabitdirmi (sıçrayış yoxdur), dəri/ağ rəngi dəyişməyib, kəskinlik həddindən çox deyil."""
    dur = probe(out)["dur"]; t = t or dur
    a = _frames(src, ss, t, fps); b = _frames(out, 0.0, t, fps); k = min(len(a), len(b)); a, b = a[:k], b[:k]
    ma = [measure(x) for x in a]; mb = [measure(y, like=x) for x, y in zip(a, b)]
    dl = np.array([y["mean_luma"] - x["mean_luma"] for x, y in zip(ma, mb)])
    mean_rgb = lambda fr: np.array([x.reshape(-1, 3).mean(0) for x in fr])
    dc = mean_rgb(b) - mean_rgb(a)
    jump = float(np.abs(np.diff(dl)).max()) if k > 1 else 0.0
    res: dict[str, Any] = {"kadr": k, "işıq_sürüşməsi_orta": round(float(dl.mean()), 2), "işıq_sürüşməsi_dalğalanma": round(float(dl.std()), 2),
                           "işıq_ən_böyük_sıçrayış": round(jump, 2), "rəng_sürüşməsi_RGB": [round(float(x), 2) for x in dc.mean(0)],
                           "rəng_dalğalanma": round(float(dc.std(0).max()), 2),
                           "kəskinlik_nisbəti": round(float(np.mean([y["sharp"] / max(x["sharp"], 1e-6) for x, y in zip(ma, mb)])), 2),
                           "səs-küy_nisbəti": round(float(np.mean([y["noise"] / max(x["noise"], 1e-6) for x, y in zip(ma, mb)])), 2)}
    sk = [(x["skin_rg"], y["skin_rg"]) for x, y in zip(ma, mb) if "skin_rg" in x and "skin_rg" in y]
    if sk: res["dəri_R/G_dəyişmə_%"] = round(float(np.mean([y / x - 1 for x, y in sk])) * 100, 2)
    bad = []
    if res["işıq_ən_böyük_sıçrayış"] > 1.5: bad.append("kadrlar arası işıq sıçrayışı")
    if res["rəng_dalğalanma"] > 1.5: bad.append("rəng dalğalanması")
    if abs(res["işıq_sürüşməsi_orta"]) > LIMITS["luma_shift"]: bad.append("işıq çox dəyişib")
    if res.get("dəri_R/G_dəyişmə_%") is not None and abs(res["dəri_R/G_dəyişmə_%"]) > LIMITS["skin_rg"] * 100: bad.append("dəri tonu dəyişib")
    if res["kəskinlik_nisbəti"] > LIMITS["sharp_ratio"]: bad.append("həddindən artıq kəskinlik")
    res["nəticə"] = "KEÇDİ" if not bad else "PROBLEM: " + ", ".join(bad)
    return res


def _grab_exact(src: Path | str, t: float, vf: str, w: int = 540, h: int = 960) -> np.ndarray:
    raw = _run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-vf", f"{vf}scale={w}:{h}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def aligned_check(src: Path | str, out: Path | str, segs: list[list[float]], cy: float = 0.45, base: dict[str, float] | None = None, hflip: bool = False,
                  exclude: list[tuple[float, float, float, float]] | None = None, skip: list[tuple[float, float]] | None = None, n: int = 14) -> dict[str, Any]:
    """Montajlı videonun yekun yoxlaması: hər nümunə kadr üçün MƏNBƏDƏ uyğun an tapılır (kəsimlər), eyni zoom/kadraj tətbiq olunur (korreksiyasız "gözlənən" kadr),
    nəticə kadrla yalnız TƏMİZ sahədə müqayisə olunur: altyazı kartı, kartlar və qrafik elementləri (`exclude` — kadrın hissələri, `skip` — tam ekran kart/qrafik vaxtları) çıxarılır.
    segs = [[mənbə_başla, mənbə_son, zoom], ...] (talk.py ilə eyni). Nəticə: orta sürüşmə (korreksiyanın təsiri) + kadrlar arası dalğalanma (sıçrayış)."""
    pre = ("hflip," if hflip else "") + (f"crop=iw*{base['s']}:ih*{base['s']}:iw*{base['cx'] - base['s'] / 2:.4f}:ih*{base['cy'] - base['s'] / 2:.4f},scale=1080:1920:flags=lanczos," if base else "")
    cand: list[tuple[float, float, float]] = []; off = 0.0
    for a, b, z in segs:
        for fr in (0.3, 0.75):
            to = off + (b - a) * fr
            if not any(s0 <= to <= s1 for s0, s1 in (skip or [])): cand.append((to, a + (b - a) * fr, z))
        off += b - a
    step = max(1, len(cand) // n); cand = cand[::step][:n]
    H, W = 960, 540; roi = np.ones((H, W), bool)
    for x0, y0, x1, y1 in (exclude or []): roi[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = False
    rows = []
    for to, ts, z in cand:
        e = _grab_exact(src, ts, f"{pre}scale=iw*{z}:ih*{z}:flags=lanczos,crop=1080:1920:(iw-1080)/2:(ih-1920)*{cy},")
        o = _grab_exact(out, to, "")
        skin, neut = _masks(e); skin &= roi; neut &= roi
        def stats(fr: np.ndarray) -> dict[str, float]:
            a = fr.astype(np.float32); y = _luma(a); g = np.abs(np.diff(y, axis=1))[:-1] + np.abs(np.diff(y, axis=0))[:, :-1]; rg = roi[:-1, :-1]
            mx, mn = a.max(-1), a.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
            d: dict[str, float] = {"luma": float(y[roi].mean()), "r": float(a[..., 0][roi].mean()), "g": float(a[..., 1][roi].mean()), "b": float(a[..., 2][roi].mean()),
                                   "sat": float(sat[roi].mean()), "p1": float(np.percentile(y[roi], 1)), "p99": float(np.percentile(y[roi], 99)), "sharp": float(np.percentile(g[rg], 99) / max(np.percentile(g[rg], 75), 0.5))}
            if skin.sum() > 200: d["skin"] = float(a[..., 0][skin].mean() / max(a[..., 1][skin].mean(), 1))
            if neut.sum() > 200: d["cast"] = float(a[..., 2][neut].mean() / max(a[..., 1][neut].mean(), 1))
            return d
        rows.append((stats(e), stats(o)))
    dl = np.array([o["luma"] - e["luma"] for e, o in rows]); dr = np.array([[o[k] - e[k] for k in "rgb"] for e, o in rows])
    sk = [o["skin"] / e["skin"] - 1 for e, o in rows if "skin" in e and "skin" in o]; ca = [o["cast"] - e["cast"] for e, o in rows if "cast" in e and "cast" in o]
    res: dict[str, Any] = {"nümunə_kadr": len(rows), "işıq_sürüşməsi_orta": round(float(dl.mean()), 2), "işıq_dalğalanma": round(float(dl.std()), 2),
                           "rəng_sürüşməsi_RGB": [round(float(x), 2) for x in dr.mean(0)], "rəng_dalğalanma": round(float(dr.std(0).max()), 2),
                           "doyma_nisbəti": round(float(np.mean([o["sat"] / max(e["sat"], 1e-6) for e, o in rows])), 3),
                           "kəskinlik_nisbəti": round(float(np.mean([o["sharp"] / max(e["sharp"], 1e-6) for e, o in rows])), 2)}
    res["qara_nöqtə_sürüşməsi"] = round(float(np.mean([o["p1"] - e["p1"] for e, o in rows])), 2); res["ağ_nöqtə_sürüşməsi"] = round(float(np.mean([o["p99"] - e["p99"] for e, o in rows])), 2)
    if sk: res["dəri_R/G_dəyişmə_%"] = round(float(np.mean(sk)) * 100, 2)
    if ca: res["ağ_balans_B/G_sürüşməsi"] = round(float(np.mean(ca)), 3)
    bad = []
    if abs(res["işıq_sürüşməsi_orta"]) > LIMITS["luma_shift"]: bad.append("işıq çox dəyişib")
    if res["işıq_dalğalanma"] > 1.5 or res["rəng_dalğalanma"] > 1.5: bad.append("kadrlar arası işıq/rəng sıçrayışı")
    if abs(res.get("dəri_R/G_dəyişmə_%", 0)) > LIMITS["skin_rg"] * 100: bad.append("dəri tonu dəyişib")
    if abs(res.get("ağ_balans_B/G_sürüşməsi", 0)) > LIMITS["neutral_cast"]: bad.append("ağ balans sürüşüb")
    if abs(res["doyma_nisbəti"] - 1) > LIMITS["sat_rel"]: bad.append("doyma dəyişib")
    if res["qara_nöqtə_sürüşməsi"] > LIMITS["black_pt"]: bad.append("qara qalxıb (bulanıq qara)")
    if -res["ağ_nöqtə_sürüşməsi"] > LIMITS["white_pt"]: bad.append("ağ solub")
    if res["kəskinlik_nisbəti"] > LIMITS["sharp_ratio"]: bad.append("həddindən artıq kəskinlik")
    res["nəticə"] = "KEÇDİ" if not bad else "PROBLEM: " + ", ".join(bad)
    return res


# ── CLI ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _cli() -> None:
    ap = argparse.ArgumentParser(prog="python -m montaj.crystal", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="təmsilçi kadrlar → qərar"); a.add_argument("video"); a.add_argument("--json", action="store_true")
    s = sub.add_parser("sample", help="hərəkətli nümunə (tam video yox) + hərəkət yoxlaması")
    s.add_argument("video"); s.add_argument("--start", type=float, default=0); s.add_argument("--dur", type=float, default=8); s.add_argument("--out", required=True)
    c = sub.add_parser("check", help="yekun render yoxlaması: orijinal vs nəticə"); c.add_argument("src"); c.add_argument("out"); c.add_argument("--start", type=float, default=0)
    k = sub.add_parser("calibrate", help="V3 referans kadrından REF ölçülərini yaz"); k.add_argument("video"); k.add_argument("--t", type=float, default=20.0)
    A = ap.parse_args()
    if A.cmd == "analyze":
        r = prepare(A.video)
        print(json.dumps(r, ensure_ascii=False, indent=1) if A.json else f"rejim: {r['mode']} ({r['source']})  parametrlər: {r['params']}\n  " + "\n  ".join(r["notes"] + r["fixes"]))
    elif A.cmd == "sample":
        r = prepare(A.video); Pch = chain(r["params"])
        _run(["ffmpeg", "-y", "-v", "error", "-ss", str(A.start), "-t", str(A.dur), "-i", A.video, "-vf", Pch, "-c:v", "libx264", "-crf", "15", "-preset", "slow",
              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", A.out])
        print(f"rejim: {r['mode']} ({r['source']})  zəncir: {Pch}")
        print(json.dumps(temporal_check(A.video, A.out, A.start, A.dur), ensure_ascii=False, indent=1))
    elif A.cmd == "check":
        print(json.dumps(temporal_check(A.src, A.out, A.start), ensure_ascii=False, indent=1))
    elif A.cmd == "calibrate":
        m = measure(grab(A.video, A.t)); REF_FILE.parent.mkdir(parents=True, exist_ok=True)
        j = json.loads(REF_FILE.read_text()) if REF_FILE.exists() else {}
        j["reference_metrics"] = {k: round(m[k], 3) for k in ("mean_luma", "sharp", "noise", "chroma_noise", "sat")}
        REF_FILE.write_text(json.dumps(j, ensure_ascii=False, indent=1)); print(j["reference_metrics"])


if __name__ == "__main__":
    _cli()
