"""Dərinlik effektləri (Premiere / CapCut tərzi) — insan maskası üzərində, yerli və pulsuz (MediaPipe + OpenCV).

Hər effekt montajın ZAMAN XƏTTİNDƏ bir pəncərədir: {"type", "start", "dur", ...}. Yalnız pəncərə daxilindəki kadrlar
emal olunur; nəticə törəmə videodur (orijinal və fon törəməsi dəyişmir), render onu avtomatik götürür.

Növlər:
  behind   — yazı İNSANIN ARXASINDA: böyük başlıq fonda, baş/çiyin hərflərin önündə.
             text, size (eni payı), y (mərkəz, hündürlük payı), color, style solid|outline, upper,
             anim stagger (hərf-hərf, standart) | rise | scale | slide | fade
  text3d   — 3D yazı: qalınlıq, yuxarıdan işıq, üzərindən parıltı keçir, perspektivdə fırlanma (hərəkət bulanıqlığı ilə).
             text, size, y, color, side (yan rəng), depth, anim swing|fly|tilt, behind (true — insanın arxasında)
  icon3d   — 3D İKON (beyin, kitablar, lampa, ürək, ulduz, təsdiq): fırlanaraq peyda olur, başın yanında, bir hissəsi
             insanın arxasında. kind brain|books|bulb|heart|star|check, size, x / y ("auto" — başa görə), color, behind, glow
  sticker  — stiker kəsik: insan bir az "qalxır", ətrafında kəskin kontur + kölgə, fon dəyişir.
             outline (eni payı), outlineColor, bg dim|color|blur|keep, bgColor, dim, lift
  focus    — yalnız FONA effekt (diqqət anı), insan toxunulmaz: bg dim|blur|gray|color|image, amount, color, file
  parallax — 2.5D kamera: insan və fon ayrı təbəqə, fərqli sürətlə yaxınlaşır. zoom (insan), bgZoom, drift
  popout   — çərçivədən çıxmaq: video brend fonunda karta kiçilir, baş kartın üst kənarından çölə çıxır.
             scale, cardTop ("auto" — başa görə), radius, color, color2, title (kartın üstündə başlıq, istəyə görə)
Ümumi: fadeIn, fadeOut (s); yazılarda integrate 0..1 (insanın kölgəsi yazıya düşür, otaq işığı, dənəvərlik).

Səs: `sfx_cues` hər effekt üçün uyğun səs anlarını verir (whoosh, zərbə, pop…) — earshot ilə yaradılır.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TYPES = ("behind", "text3d", "icon3d", "sticker", "focus", "parallax", "popout")
COMMON = {"fadeIn": 0.35, "fadeOut": 0.35}
DEFAULTS: dict[str, dict[str, Any]] = {
    "behind": {"size": 0.2, "y": 0.3, "style": "solid", "upper": True, "anim": "stagger", "font": "Montserrat", "weight": 800,
               "maxWidth": 0.94, "integrate": 0.8},
    "text3d": {"size": 0.21, "y": 0.28, "anim": "swing", "behind": True, "depth": 0.03, "font": "Montserrat", "weight": 800,
               "upper": True, "maxWidth": 0.9, "integrate": 0.8},
    "icon3d": {"kind": "brain", "size": 0.44, "x": "auto", "y": "auto", "behind": True, "glow": 0.3, "integrate": 0.7,
               "fadeIn": 0.0, "fadeOut": 0.0},
    "sticker": {"outline": 0.011, "outlineColor": "#FFFFFF", "bg": "dim", "dim": 0.6, "shadow": True, "lift": 0.03},
    "focus": {"bg": "dim", "amount": 0.6},
    "parallax": {"zoom": 0.09, "bgZoom": 0.02, "drift": 0.015, "fadeOut": 0.7},
    "popout": {"scale": 0.8, "cardTop": "auto", "radius": 0.045, "shadow": True, "fadeIn": 0.55, "fadeOut": 0.5,
               "font": "Montserrat", "weight": 800, "titleSize": 0.085, "upper": True},
}
NEEDS_TEXT = ("behind", "text3d")


# ---------------------------------------------------------------------------
# Seçimlər
# ---------------------------------------------------------------------------

def normalize(e: dict[str, Any], theme: dict[str, Any] | None = None) -> dict[str, Any]:
    t = e.get("type")
    if t not in TYPES:
        raise ValueError(f"naməlum effekt: {t} ({', '.join(TYPES)})")
    th = theme or {}
    s = {**COMMON, **DEFAULTS[t], **{k: v for k, v in e.items() if v is not None}}
    if "start" not in s or "dur" not in s:
        raise ValueError("effekt üçün start və dur lazımdır (zaman xəttində, saniyə)")
    s["start"], s["dur"] = float(s["start"]), float(s["dur"])
    if s["dur"] <= 0.2:
        raise ValueError("dur 0.2 s-dən uzun olmalıdır")
    if t in NEEDS_TEXT and not str(s.get("text") or "").strip():
        raise ValueError(f"{t} üçün text lazımdır")
    primary, deep = th.get("primary") or "#E8E8E8", th.get("primaryDeep") or "#333333"
    if t == "behind":
        s.setdefault("color", "#FFFFFF" if s["style"] == "outline" else primary)
    if t == "text3d":
        s.setdefault("color", primary)
        s.setdefault("side", deep)
    if t == "icon3d":
        from montaj import icons3d

        if s["kind"] not in icons3d.KINDS:
            raise ValueError(f"naməlum ikon: {s['kind']} ({', '.join(icons3d.KINDS)})")
    if t == "sticker":
        s.setdefault("bgColor", deep)
    if t == "focus" and s["bg"] == "color":
        s.setdefault("color", deep)
    if t == "focus" and s["bg"] == "image" and not (s.get("file") and Path(s["file"]).is_file()):
        raise ValueError(f"focus image üçün fayl tapılmadı: {s.get('file')}")
    if t == "popout":
        s.setdefault("color", primary)
        s.setdefault("color2", deep)
        s.setdefault("titleColor", "#FFFFFF")
    s["fadeIn"], s["fadeOut"] = min(float(s["fadeIn"]), s["dur"] / 2), min(float(s["fadeOut"]), s["dur"] / 2)
    return s


def effects_key(effects: list[dict[str, Any]], src: Path) -> str:
    st = src.stat()
    h = hashlib.sha1(json.dumps(effects, sort_keys=True, ensure_ascii=False).encode())
    h.update(f"{src.name}:{st.st_size}:{int(st.st_mtime)}:v3".encode())
    return h.hexdigest()[:10]


# ---------------------------------------------------------------------------
# Vaxt
# ---------------------------------------------------------------------------

def src_to_timeline(spans: list[tuple[float, float, float]], ts: float) -> list[float]:
    """spans: (srcIn, srcOut, tlStart). Mənbə vaxtı ts-in zaman xəttindəki bütün yerləri."""
    return [tl + (ts - a) for a, b, tl in spans if a - 1e-6 <= ts < b + 1e-6]


def envelope(e: dict[str, Any], tl: float) -> float:
    lt = tl - e["start"]
    if lt < 0 or lt > e["dur"]:
        return 0.0
    a = _sm(lt / e["fadeIn"]) if e["fadeIn"] > 0 else 1.0
    b = _sm((e["dur"] - lt) / e["fadeOut"]) if e["fadeOut"] > 0 else 1.0
    return float(min(a, b))


def _out_phase(e: dict[str, Any], lt: float) -> float:
    """Çıxış mərhələsi 0..1 (0 — hələ çıxmır)."""
    return 1 - _sm((e["dur"] - lt) / e["fadeOut"]) if e["fadeOut"] > 0 else 0.0


def _sm(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _ease_out(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def _ease_back(x: float, k: float = 1.6) -> float:
    x = min(1.0, max(0.0, x)) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def _ease_in_out(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# ---------------------------------------------------------------------------
# Maska: saç səviyyəsində kənar (guided filter — kənar kadrın özünü izləyir)
# ---------------------------------------------------------------------------

def matte(f8: np.ndarray, ms: np.ndarray) -> np.ndarray:
    """Kiçik seqmentasiya maskası → tam ölçüdə, kənarı kadra yapışan (saç, qulaq, çiyin) yumşaq maska."""
    H, W = f8.shape[:2]
    gw, gh = W // 2, H // 2
    guide = cv2.resize(f8, (gw, gh), interpolation=cv2.INTER_AREA)
    m = cv2.resize(ms.astype(np.float32), (gw, gh), interpolation=cv2.INTER_LINEAR)
    try:
        m = cv2.ximgproc.guidedFilter(guide, m, radius=max(4, gw // 90), eps=60.0)
    except AttributeError:  # opencv-contrib yoxdursa — sadə yumşaltma
        m = cv2.GaussianBlur(m, (0, 0), 1.5)
    m = np.clip((m - 0.06) / 0.88, 0, 1)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)


# ---------------------------------------------------------------------------
# Yazı: hərf spraytları
# ---------------------------------------------------------------------------

def az_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def _rgb(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hex01(c: str) -> np.ndarray:
    return np.array(_rgb(c), np.float32) / 255.0


def _font(e: dict[str, Any], px: int) -> ImageFont.FreeTypeFont:
    from montaj import fonts

    path = fonts.ttf_path(e.get("font"), e.get("weight")) or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(path, px)


def _fit_font(e: dict[str, Any], text: str, W: int, size: float, max_w: float) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    lines = text.split("\n")
    px = max(12, int(W * size))
    while True:
        font = _font(e, px)
        if max(font.getlength(ln) for ln in lines) <= W * max_w or px <= 14:
            return font, lines
        px = int(px * 0.94)


def glyphs(e: dict[str, Any], W: int, text_key: str = "text", size_key: str = "size", color_key: str = "color",
           max_w: float | None = None) -> dict[str, Any]:
    """Mətnin hər hərfi ayrıca sprayt: [(RGBA float, x, y)] bloka nisbətən + blokun ölçüsü (sətirlər mərkəzdə)."""
    text = az_upper(e[text_key]) if e.get("upper") else e[text_key]
    font, lines = _fit_font(e, text, W, float(e[size_key]), float(max_w or e.get("maxWidth", 0.94)))
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * 0.92)
    stroke = max(2, int(font.size * 0.035)) if e.get("style") == "outline" else 0
    col = _rgb(e[color_key]) + (255,)
    out, bw = [], 0.0
    for li, ln in enumerate(lines):
        lw = font.getlength(ln)
        bw = max(bw, lw)
        for i, ch in enumerate(ln):
            if ch == " ":
                continue
            x = font.getlength(ln[:i])
            l, t, r, b = font.getbbox(ch, stroke_width=stroke)
            pad = 6 + stroke
            im = Image.new("RGBA", (int(r - l) + pad * 2, int(b - t) + pad * 2), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((pad - l, pad - t), ch, font=font, fill=col if not stroke else (0, 0, 0, 0),
                                    stroke_width=stroke, stroke_fill=col)
            out.append({"spr": np.asarray(im, np.float32) / 255.0, "x": x + l - pad, "y": li * lh + t - pad, "lw": lw})
    for g in out:
        g["x"] += (bw - g["lw"]) / 2
    return {"glyphs": out, "w": bw, "h": lh * (len(lines) - 1) + asc + desc}


def text_sprite(e: dict[str, Any], W: int) -> Image.Image:
    """Bütöv yazı spraytı (3D və sadə animasiyalar üçün)."""
    g = glyphs(e, W)
    w, h = int(g["w"]) + 24, int(g["h"]) + 24
    rgb, a = np.zeros((h, w, 3), np.float32), np.zeros((h, w), np.float32)
    for gl in g["glyphs"]:
        _paste(rgb, a, gl["spr"], int(gl["x"]) + 12, int(gl["y"]) + 12)
    rgba = np.dstack([rgb, a])
    return Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def extruded_sprite(e: dict[str, Any], W: int) -> tuple[np.ndarray, np.ndarray]:
    """3D yazı: arxa təbəqələr (yan üz, dərinə doğru tündləşir) + ön üz (yuxarıdan işıq, kənar parıltısı).
    Qaytarır: RGBA float32 və ön üzün alfa maskası (eyni ölçüdə — parıltı keçidi üçün)."""
    flat = text_sprite({**e, "style": "solid"}, W)
    fw, fh = flat.size
    depth = max(3, int(W * float(e["depth"])))
    dx, dy = 0.55, 0.85
    ox, oy = int(depth * dx) + 2, int(depth * dy) + 2
    out = np.zeros((fh + oy + 2, fw + ox + 2, 4), np.float32)
    a = np.asarray(flat, dtype=np.float32)[..., 3] / 255.0
    side = _hex01(e["side"])
    for k in range(depth, 0, -1):
        x, y = int(round(k * dx)), int(round(k * dy))
        shade = 0.45 + 0.55 * (1 - k / depth) ** 1.4  # dərinə doğru tündləşir
        reg = out[y:y + fh, x:x + fw]
        reg[..., :3] = reg[..., :3] * (1 - a[..., None]) + side * shade * a[..., None]
        reg[..., 3] = np.maximum(reg[..., 3], a)
    front = _hex01(e["color"])
    grad = np.linspace(1.2, 0.82, fh, dtype=np.float32)[:, None, None]
    face = np.clip(front * grad, 0, 1)
    er = cv2.erode((a > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=max(1, fh // 110))
    rim = cv2.GaussianBlur(np.clip(a - er.astype(np.float32), 0, 1), (0, 0), 1.0)[..., None]
    face = np.clip(face * (1 - rim * 0.3) + rim * 0.42, 0, 1)
    reg = out[0:fh, 0:fw]
    reg[..., :3] = reg[..., :3] * (1 - a[..., None]) + face * a[..., None]
    reg[..., 3] = np.maximum(reg[..., 3], a)
    fa = np.zeros(out.shape[:2], np.float32)
    fa[0:fh, 0:fw] = a
    return out, fa


# ---------------------------------------------------------------------------
# Kompozisiya köməkçiləri (float32, 0..1)
# ---------------------------------------------------------------------------

def _paste(canvas_rgb: np.ndarray, canvas_a: np.ndarray, spr: np.ndarray, x: int, y: int, alpha: float = 1.0) -> None:
    H, W = canvas_a.shape
    sh, sw = spr.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + sw), min(H, y + sh)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * alpha
    canvas_rgb[y0:y1, x0:x1] = canvas_rgb[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a
    canvas_a[y0:y1, x0:x1] = 1 - (1 - canvas_a[y0:y1, x0:x1]) * (1 - a[..., 0])


def _shift(a: np.ndarray, dy: int, dx: int = 0) -> np.ndarray:
    """Təbəqəni sürüşdürür (kənar o biri tərəfə keçmir)."""
    H, W = a.shape[:2]
    return cv2.warpAffine(a, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def _vblur(spr: np.ndarray, k: int) -> np.ndarray:
    """Şaquli hərəkət bulanıqlığı (sürətlə qalxan hərf)."""
    if k < 2:
        return spr
    pad = np.zeros((k, spr.shape[1], 4), np.float32)
    return cv2.blur(np.vstack([pad, spr, pad]), (1, k))


def _gray(f: np.ndarray) -> np.ndarray:
    g = f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114
    return np.repeat(g[..., None], 3, axis=2)


def _blur(f: np.ndarray, sigma: float) -> np.ndarray:
    H, W = f.shape[:2]
    small = cv2.resize(f, (max(8, W // 4), max(8, H // 4)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), max(0.5, sigma / 4))
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)


def _cover(img: Image.Image, W: int, H: int) -> np.ndarray:
    s = max(W / img.width, H / img.height)
    im = img.convert("RGB").resize((max(W, int(img.width * s + 0.5)), max(H, int(img.height * s + 0.5))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return np.asarray(im.crop((x, y, x + W, y + H)), np.float32) / 255.0


def _fill_behind(f: np.ndarray, m: np.ndarray) -> np.ndarray:
    """İnsanın arxasındakı fonu təxmini bərpa edir (inpaint, kiçik ölçüdə)."""
    H, W = m.shape
    sw, sh = max(16, W // 4), max(16, H // 4)
    small = (cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)
    hole = cv2.dilate((cv2.resize(m, (sw, sh)) > 0.2).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    fill = cv2.inpaint(small, hole, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
    fill = cv2.resize(cv2.GaussianBlur(fill, (0, 0), 2), (W, H), interpolation=cv2.INTER_LINEAR)
    md = cv2.GaussianBlur(cv2.resize(hole.astype(np.float32) / 255.0, (W, H)), (0, 0), 6)[..., None]
    return f * (1 - md) + fill * md


def _bg_variant(f: np.ndarray, kind: str, e: dict[str, Any], cache: dict[str, Any], amount: float) -> np.ndarray:
    H, W = f.shape[:2]
    if kind == "dim":
        return f * (1 - amount)
    if kind == "blur":  # insanın yeri əvvəlcə fonla doldurulur — bulanıqda insanın "kölgəsi" (hale) qalmasın
        base = _fill_behind(f, cache["mask"]) if cache.get("mask") is not None else f
        return _blur(base, 8 + 40 * amount) * (1 - 0.15 * amount)
    if kind == "gray":
        return _gray(f) * (1 - 0.25 * amount)
    if kind == "color":
        return np.broadcast_to(_hex01(e.get("color") or "#222222"), f.shape)
    if kind == "image":
        if "img" not in cache:
            cache["img"] = _cover(Image.open(e["file"]), W, H)
        return cache["img"]
    return f


def _integrate(rgb: np.ndarray, a: np.ndarray, f: np.ndarray, m: np.ndarray, k: float, seed: int) -> np.ndarray:
    """Yazını səhnəyə "oturdur": insanın yumşaq kölgəsi yazıya düşür, parlaqlıq otaq işığına uyğunlaşır, kameranın
    dənəvərliyi. a — yazının alfası (dəyişmir); qaytarılan — yazının yeni rəngi."""
    if k <= 0 or not (a > 0.01).any():
        return rgb
    H, W = m.shape
    ys, xs = np.where(a > 0.01)
    y0, y1 = max(0, ys.min() - 4), min(H, ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(W, xs.max() + 5)
    sl = (slice(y0, y1), slice(x0, x1))
    sh = _shift(cv2.GaussianBlur(m, (0, 0), W * 0.022), int(W * 0.022), int(W * 0.01))[sl] * 0.55 * k
    L = cv2.GaussianBlur(f[..., 1], (0, 0), W * 0.06)[sl]
    gain = 0.86 + 0.15 * np.clip(L / max(float(L.mean()), 1e-3), 0, 2)
    r = rgb[sl] * (1 - sh[..., None]) * (1 - 0.25 * k + 0.25 * k * gain[..., None])
    noise = np.random.default_rng(seed).normal(0, 0.012 * k, r.shape[:2]).astype(np.float32)[..., None]
    out = rgb.copy()
    out[sl] = np.clip(r + noise, 0, 1)
    return out


def _draw_glyphs(rgb: np.ndarray, a: np.ndarray, gl: dict[str, Any], x0: float, y0: float, lt: float, H: int,
                 out_phase: float = 0.0, stagger: float = 0.045, rise: float = 0.055) -> None:
    """Hərf-hərf giriş: hər hərf aşağıdan qalxır (ease-back), sürətli anda hərəkət bulanıqlığı; çıxışda yuxarı süzülür."""
    n = len(gl["glyphs"])
    for i, g in enumerate(gl["glyphs"]):
        ti = lt - i * stagger
        if ti <= 0:
            continue
        p = _ease_back(ti / 0.5, 1.7)
        dy = (1 - p) * H * rise - out_phase * H * 0.025
        alpha = min(1.0, ti / 0.16) * (1 - out_phase * (0.4 + 0.6 * (i / max(1, n - 1))))
        vel = abs(_ease_back((ti + 0.02) / 0.5, 1.7) - p) * H * rise
        spr = _vblur(g["spr"], int(vel * 1.2))
        off = (spr.shape[0] - g["spr"].shape[0]) // 2
        _paste(rgb, a, spr, int(x0 + g["x"]), int(y0 + g["y"] + dy) - off, max(0.0, alpha))


# ---------------------------------------------------------------------------
# Effektlər (kadr, maska, effekt, yerli vaxt, zərf, keş) → kadr
# ---------------------------------------------------------------------------

def fx_behind(f, m, e, lt, env, cache):
    H, W = m.shape
    anim = e.get("anim", "stagger")
    rgb, a = np.zeros_like(f), np.zeros(m.shape, np.float32)
    if anim == "stagger":
        if "gl" not in cache:
            cache["gl"] = glyphs(e, W)
        gl = cache["gl"]
        _draw_glyphs(rgb, a, gl, (W - gl["w"]) / 2, H * float(e["y"]) - gl["h"] / 2, lt, H, _out_phase(e, lt))
        vis = a
    else:
        if "spr" not in cache:
            cache["spr"] = np.asarray(text_sprite(e, W), np.float32) / 255.0
        spr = cache["spr"]
        k = _ease_out(lt / 0.7)
        sc = 0.82 + 0.18 * _ease_back(lt / 0.6) if anim == "scale" else 1.0
        s = spr if abs(sc - 1) < 1e-3 else cv2.resize(spr, (max(2, int(spr.shape[1] * sc)), max(2, int(spr.shape[0] * sc))))
        x = (W - s.shape[1]) // 2 + (int(-W * 0.35 * (1 - k)) if anim == "slide" else 0)
        y = int(H * float(e["y"]) - s.shape[0] / 2) + (int(H * 0.05 * (1 - k)) if anim == "rise" else 0)
        _paste(rgb, a, s, x, y)
        vis = a * env
    rgb = _integrate(rgb, a, f, m, float(e.get("integrate", 0.8)), int(lt * 1000))
    vis = vis * (1 - m)
    return f * (1 - vis[..., None]) + rgb * vis[..., None]


def _perspective(w: int, h: int, ry: float, rx: float, scale: float) -> tuple[np.ndarray, np.ndarray]:
    f = 2.4 * max(w, h)
    pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        X, Z = x * math.cos(ry), x * math.sin(ry)
        Y, Z = y * math.cos(rx) - Z * math.sin(rx), y * math.sin(rx) + Z * math.cos(rx)
        pts.append((X * f / (f + Z) * scale, Y * f / (f + Z) * scale))
    return np.float32([(0, 0), (w, 0), (w, h), (0, h)]), np.float32(pts)


def _pose3d(anim: str, lt: float) -> tuple[float, float, float]:
    t_in = lt / 0.9
    if anim == "fly":
        return 0.15 * math.sin(lt * 1.3), math.radians(55) * (1 - _ease_out(t_in)), 0.35 + 0.65 * _ease_back(t_in, 1.2)
    if anim == "tilt":
        return math.radians(-16) + 0.12 * math.sin(lt * 0.9), math.radians(8), 1.0
    ry = math.radians(75) * (1 - _ease_back(t_in, 1.4)) + math.radians(7) * math.sin(lt * 1.4) * _sm(t_in)
    return ry, math.radians(6) * math.sin(lt * 0.8), 0.7 + 0.3 * _ease_out(t_in)


def fx_text3d(f, m, e, lt, env, cache):
    H, W = m.shape
    if "spr" not in cache:
        cache["spr"], cache["face"] = extruded_sprite(e, W)
    base, face = cache["spr"], cache["face"]
    sh_, sw_ = base.shape[:2]
    b = (lt - 0.55) / 0.75 * 1.6 - 0.3  # parıltı keçidi: ön üzün üzərindən diaqonal işıq zolağı
    spr = base
    if -0.3 < b < 1.3:
        yy, xx = np.mgrid[0:sh_, 0:sw_].astype(np.float32)
        band = np.exp(-(((xx / sw_) + 0.35 * (yy / sh_) - b) ** 2) / 0.0035) * 0.55 * face
        spr = base.copy()
        spr[..., :3] = np.clip(spr[..., :3] + band[..., None], 0, 1)
    anim = e.get("anim", "swing")
    cx, cy = W / 2, H * float(e["y"])
    samples = (-1 / 75, 0.0, 1 / 75) if lt < 0.9 else (0.0,)  # hərəkət bulanıqlığı — sürətli girişdə
    acc = np.zeros((H, W, 4), np.float32)
    for dt in samples:
        ry, rx, sc = _pose3d(anim, max(0.0, lt + dt))
        src, dst = _perspective(sw_, sh_, ry, rx, sc)
        M = cv2.getPerspectiveTransform(src, dst + np.float32([cx, cy]))
        w4 = cv2.warpPerspective(spr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        w4[..., :3] *= w4[..., 3:4]  # premultiplied — bulanıqlıqda qara kənar olmasın
        acc += w4
    warped = acc / len(samples)
    a = warped[..., 3]
    col = warped[..., :3] / np.maximum(a[..., None], 1e-4)
    col = _integrate(col, a, f, m, float(e.get("integrate", 0.8)), int(lt * 1000))
    a = a * env
    sh = _shift(cv2.GaussianBlur(warped[..., 3], (0, 0), W * 0.012), int(W * 0.014), int(W * 0.006)) * 0.38 * env
    if e.get("behind", True):
        a, sh = a * (1 - m), sh * (1 - m)
    out = f * (1 - sh[..., None])
    return out * (1 - a[..., None]) + col * a[..., None]


def fx_icon3d(f, m, e, lt, env, cache):
    """3D ikon (Three.js kadrları, giriş/çıxış animasiyası kadrlarda) — standart olaraq insanın arxasında, yanında."""
    H, W = m.shape
    if "fr" not in cache:
        from montaj import icons3d

        px = int(min(760, max(120, W * float(e["size"])))) // 2 * 2
        cache["fr"] = icons3d.frames(e["kind"], e.get("color"), e["dur"], px)
        ys, xs = np.where(m > 0.5)
        pcx, top = (float(xs.mean()) / W, float(ys.min()) / H) if len(xs) else (0.5, 0.3)
        half = float(e["size"]) / 2
        x = e["x"] if e["x"] != "auto" else (pcx + 0.25 if pcx <= 0.5 else pcx - 0.25)  # başın yanında, bir hissəsi arxada
        y = e["y"] if e["y"] != "auto" else top + 0.01
        cache["pos"] = (min(1 - half * 0.75, max(half * 0.75, float(x))), max(half * W / H * 0.8, float(y)))
    fr = cache["fr"]
    spr = fr[min(len(fr) - 1, int(round(lt * 30)))].astype(np.float32) / 255.0
    cx, cy = cache["pos"]
    rgb, a = np.zeros_like(f), np.zeros(m.shape, np.float32)
    _paste(rgb, a, spr, int(cx * W - spr.shape[1] / 2), int(cy * H - spr.shape[0] / 2))
    if not (a > 0.01).any():
        return f
    occ = (1 - m) if e.get("behind", True) else 1.0
    out = f
    g = float(e.get("glow") or 0)
    if g > 0:  # ikonun arxasında yumşaq işıq — tünd fonda ayrılsın
        halo = cv2.GaussianBlur(a, (0, 0), W * 0.05) * g * occ
        tintc = (rgb * a[..., None]).sum(axis=(0, 1)) / max(float(a.sum()), 1e-3)
        out = np.clip(out + halo[..., None] * tintc, 0, 1)
    sh = _shift(cv2.GaussianBlur(a, (0, 0), W * 0.014), int(W * 0.016), int(W * 0.008)) * 0.35 * occ
    out = out * (1 - sh[..., None])
    rgb = _integrate(rgb, a, f, m, float(e.get("integrate", 0.7)), int(lt * 1000))
    vis = (a * occ)[..., None]
    return out * (1 - vis) + rgb * vis


def _dilate(m: np.ndarray, r: int) -> np.ndarray:
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    d = cv2.dilate((m > 0.5).astype(np.uint8), k)
    return cv2.GaussianBlur(d.astype(np.float32), (0, 0), max(1.0, r * 0.12))


def _person_center(m: np.ndarray) -> tuple[float, float]:
    ys, xs = np.where(m > 0.5)
    H, W = m.shape
    return (float(xs.mean()), float(ys.min() + (ys.max() - ys.min()) * 0.4)) if len(xs) else (W / 2, H * 0.45)


def _scale_about(img: np.ndarray, s: float, cx: float, cy: float, dx: float = 0.0, border=cv2.BORDER_REFLECT) -> np.ndarray:
    M = np.float32([[s, 0, (1 - s) * cx + dx], [0, s, (1 - s) * cy]])
    H, W = img.shape[:2]
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)


def fx_sticker(f, m, e, lt, env, cache):
    H, W = m.shape
    if "c" not in cache:
        cache["c"] = _person_center(m)
    cx, cy = cache["c"]
    lift = 1 + float(e.get("lift", 0.03)) * _ease_back(lt / 0.35, 2.4) * env  # insan bir az "qalxır"
    fp, mp = _scale_about(f, lift, cx, cy), _scale_about(m, lift, cx, cy, border=cv2.BORDER_CONSTANT)
    r = max(2, int(W * float(e["outline"]) * min(1.0, _ease_back(lt / 0.3, 2.0))))
    d = np.clip((_dilate(mp, r) - 0.35) / 0.3, 0, 1)  # kəskin, hamar kontur (yumşaq hale yox)
    d = np.maximum(d, mp)
    cache["mask"] = m
    bg = _bg_variant(f, e.get("bg", "dim"), {**e, "color": e.get("bgColor")}, cache, float(e.get("dim", 0.6)))
    out = np.array(bg, np.float32, copy=True)
    if e.get("shadow", True):
        sh = _shift(cv2.GaussianBlur(d, (0, 0), W * 0.016), int(W * 0.018), int(W * 0.006)) * 0.5
        out = out * (1 - sh[..., None])
    oc = _hex01(e.get("outlineColor", "#FFFFFF"))
    out = out * (1 - d[..., None]) + oc * d[..., None]
    out = out * (1 - mp[..., None]) + fp * mp[..., None]
    return f * (1 - env) + out * env


def fx_focus(f, m, e, lt, env, cache):
    cache["mask"] = m
    bg = _bg_variant(f, e.get("bg", "dim"), e, cache, float(e.get("amount", 0.6)))
    out = bg * (1 - m[..., None]) + f * m[..., None]
    return f * (1 - env) + out * env


def fx_parallax(f, m, e, lt, env, cache):
    H, W = m.shape
    q = _ease_in_out(lt / e["dur"]) * env
    cx, cy = _person_center(m)
    bg = _scale_about(_fill_behind(f, m), 1 + float(e["bgZoom"]) * q, W / 2, H / 2, -W * float(e["drift"]) * q)
    s = 1 + float(e["zoom"]) * q
    fp, mp = _scale_about(f, s, cx, cy), _scale_about(m, s, cx, cy, border=cv2.BORDER_CONSTANT)
    return bg * (1 - mp[..., None]) + fp * mp[..., None]


def _round_mask(w: int, h: int, r: int) -> np.ndarray:
    ss = 2  # hamar künclər
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius=r * ss, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255.0


def fx_popout(f, m, e, lt, env, cache):
    H, W = m.shape
    if "canvas" not in cache:
        c1, c2 = _hex01(e["color"]), _hex01(e["color2"])
        t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        glow = np.exp(-(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H * 0.3) / (H * 0.45)) ** 2))[..., None] * 0.12
        cache["canvas"] = np.clip(c1 * (1 - t) + c2 * t + glow, 0, 1).astype(np.float32)
        rows = np.where((m > 0.5).mean(axis=1) > 0.04)[0]  # ən azı baş genişliyi — maskadakı kiçik ləkələr sayılmır
        cache["top"] = rows[0] / H if len(rows) else 0.2
    k = _ease_in_out(env)  # keçid — həndəsi kiçilmə (kadrların üst-üstə qarışması yox)
    s = 1 - (1 - float(e["scale"])) * k
    sw, sh = max(2, int(W * s)), max(2, int(H * s))
    x0 = (W - sw) // 2
    y0 = max(0, min(H - sh, int(H / 2 - sh / 2 + H * 0.06 * k)))
    fs = cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA)
    ms = cv2.resize(m, (sw, sh), interpolation=cv2.INTER_LINEAR)
    ct = e["cardTop"]
    if ct == "auto":  # kartın üst kənarı gözlərin bir az yuxarısından keçir — baş kartdan çölə çıxır
        ct = min(0.45, max(0.1, cache["top"] + 0.13))
    cut = int(sh * float(ct) * k)
    out = cache["canvas"].copy()
    card = _round_mask(sw, sh - cut, max(1, int(W * float(e["radius"]) * k)))
    if e.get("shadow", True) and k > 0.01:
        shadow = np.zeros((H, W), np.float32)
        shadow[y0 + cut:y0 + sh, x0:x0 + sw] = card
        shadow = _shift(cv2.GaussianBlur(shadow, (0, 0), W * 0.025), int(W * 0.025)) * 0.45 * k
        out = out * (1 - shadow[..., None])
    reg = out[y0 + cut:y0 + sh, x0:x0 + sw]
    a = card[..., None]
    reg[:] = reg * (1 - a) + fs[cut:] * a
    if k > 0.01:  # kartdan çıxan başın fona yumşaq kölgəsi — havada "üzməsin"
        above = ms.copy()
        above[cut:] = 0
        ps = np.zeros((H, W), np.float32)
        ps[y0:y0 + sh, x0:x0 + sw] = above
        ps = _shift(cv2.GaussianBlur(ps, (0, 0), W * 0.015), int(W * 0.015)) * 0.35 * k
        out = out * (1 - ps[..., None])
    pa = ms[..., None]
    sub = out[y0:y0 + sh, x0:x0 + sw]
    sub[:] = sub * (1 - pa) + fs * pa
    if e.get("title") and k > 0.05:
        if "tg" not in cache:
            cache["tg"] = glyphs({**e, "style": "solid"}, W, "title", "titleSize", "titleColor", 0.86)
        gl = cache["tg"]
        head_top = y0 + int(sh * cache["top"])
        rgb, ta = np.zeros_like(out), np.zeros((H, W), np.float32)
        _draw_glyphs(rgb, ta, gl, (W - gl["w"]) / 2, max(H * 0.04, head_top / 2 - gl["h"] / 2), lt - 0.25, H,
                     _out_phase(e, lt))
        out = out * (1 - ta[..., None]) + rgb * ta[..., None]
    return out


FX: dict[str, Callable] = {"behind": fx_behind, "text3d": fx_text3d, "icon3d": fx_icon3d, "sticker": fx_sticker, "focus": fx_focus,
                           "parallax": fx_parallax, "popout": fx_popout}
ORDER = {"focus": 0, "sticker": 1, "behind": 2, "text3d": 2, "icon3d": 2, "parallax": 3, "popout": 4}  # fon → yazı → kamera → çərçivə


def apply_frame(f8: np.ndarray, m: np.ndarray, effects: list[dict[str, Any]], tls: list[float],
                caches: list[dict[str, Any]]) -> np.ndarray:
    """Bir kadra bütün aktiv effektlər. f8 — uint8 RGB, m — tam ölçüdə maska."""
    f = f8.astype(np.float32) / 255.0
    for i in sorted(range(len(effects)), key=lambda j: ORDER[effects[j]["type"]]):
        e = effects[i]
        tl = next((t for t in tls if envelope(e, t) > 0), None)
        if tl is None:
            continue
        f = FX[e["type"]](f, m, e, tl - e["start"], envelope(e, tl), caches[i])
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------------------
# Səs effektləri (hər effektə uyğun; earshot ilə yaradılır)
# ---------------------------------------------------------------------------

SFX_SOUNDS = {  # ad → (earshot səsi, seed); montajda `sfx_<ad>` media kimi
    "fx_whoosh": ("whoosh/fast", 11), "fx_whoosh_soft": ("whoosh/soft", 12), "fx_hit": ("boom/deep", 13),
    "fx_pop": ("pop/soft", 14), "fx_rise": ("rise/reverse", 15), "fx_down": ("downlifter/air_fall", 16),
}


def sfx_cues(effects: list[dict[str, Any]], peaks: dict[str, float] | None = None) -> list[dict[str, Any]]:
    """Effektlərin səs anları: [{"kind", "t" (səsin başlanğıcı), "vol"}]. peaks — səsin ən güclü anının ofseti
    (whoosh-un pik anı hərəkətin ən sürətli anına düşsün)."""
    pk = peaks or {}
    out: list[dict[str, Any]] = []

    def at_peak(kind: str, t: float, vol: float) -> None:
        out.append({"kind": kind, "t": round(max(0.0, t - pk.get(kind, 0.0)), 3), "vol": vol})

    def at_onset(kind: str, t: float, vol: float) -> None:
        out.append({"kind": kind, "t": round(max(0.0, t - 0.01), 3), "vol": vol})
    for e in effects:
        s, d, t = e["start"], e["dur"], e["type"]
        if t == "behind":
            at_peak("fx_whoosh_soft", s + 0.22, 0.35)
        elif t == "text3d":
            at_peak("fx_whoosh", s + 0.45, 0.35)
            at_onset("fx_hit", s + 0.75, 0.4)
        elif t == "icon3d":
            at_peak("fx_whoosh_soft", s + 0.2, 0.3)
            at_onset("fx_pop", s + 0.3, 0.4)
        elif t == "sticker":
            at_onset("fx_pop", s, 0.45)
        elif t == "focus":
            at_onset("fx_down", s, 0.25)
        elif t == "parallax":
            at_peak("fx_rise", s + min(d * 0.6, 1.5), 0.22)
        elif t == "popout":
            at_peak("fx_whoosh", s + 0.35, 0.3)
            at_onset("fx_pop", s + e["fadeIn"], 0.35)
    return sorted(out, key=lambda c: c["t"])


def make_sfx(lib: Path, earshot: str) -> dict[str, float]:
    """Kitabxanada fx_*.wav (yoxdursa earshot ilə) + hər səsin pik ofseti."""
    lib.mkdir(parents=True, exist_ok=True)
    peaks = {}
    for kind, (sound, seed) in SFX_SOUNDS.items():
        p = lib / f"{kind}.wav"
        if not p.is_file():
            tmp = lib / f"{kind}.part.wav"
            subprocess.run([earshot, "make", "x", "--sound", sound, "-o", str(tmp), "--seed", str(seed), "--lufs", "-16"],
                           check=True, capture_output=True)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ac", "2", "-ar", "48000", str(p)], check=True)
            tmp.unlink(missing_ok=True)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
        a = np.abs(np.frombuffer(raw[: len(raw) // 2 * 2], "<i2").astype(np.float32))
        env = np.convolve(a, np.ones(160) / 160, mode="same") if len(a) else a
        peaks[kind] = float(np.argmax(env) / 8000) if len(env) else 0.0
    return peaks


# ---------------------------------------------------------------------------
# Tam emal
# ---------------------------------------------------------------------------

def process(src: Path, dst: Path, effects: list[dict[str, Any]], spans: list[tuple[float, float, float]],
            model: str = "accurate", smooth: float = 0.45, progress=lambda n: None,
            max_frames: int | None = None, ss: float = 0.0) -> dict[str, Any]:
    """Mənbə videonu kadr-kadr oxuyur; effekt pəncərəsindəki kadrlara maska + effekt, qalanları olduğu kimi.
    Nəticə — eyni ölçü, fps, kadr sayı (səssiz H.264)."""
    from montaj import background

    info = background.probe(src)
    W, H, fps = info["w"] // 2 * 2, info["h"] // 2 * 2, info["fps"]
    num, den = (fps.split("/") + ["1"])[:2]
    rate = float(num) / float(den or 1)
    sw = 540 if W <= H else 960
    sh = int(round(sw * H / W / 2) * 2)
    seg = background.Segmenter(model)
    caches: list[dict[str, Any]] = [{} for _ in effects]
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".part.mp4")
    wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", fps,
                           "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                           "-r", fps, str(tmp)], stdin=subprocess.PIPE)
    prev, n, touched = None, 0, 0
    try:
        for f8 in background._frames(src, W, H, fps, ss):
            ts = ss + n / rate
            tls = src_to_timeline(spans, ts)
            active = [e for e in effects if any(envelope(e, t) > 0 for t in tls)]
            if active:
                small = cv2.resize(f8, (sw, sh), interpolation=cv2.INTER_AREA)
                ms = background.refine(seg.person(small), prev, smooth)
                prev = ms
                f8 = apply_frame(f8, matte(f8, ms), effects, tls, caches)
                touched += 1
            else:
                prev = None
            wr.stdin.write(np.ascontiguousarray(f8).tobytes())
            n += 1
            if n % 30 == 0:
                progress(n)
            if max_frames and n >= max_frames:
                break
    finally:
        wr.stdin.close()
        rc = wr.wait()
        seg.close()
    if rc != 0 or not tmp.is_file():
        raise RuntimeError("effekt videosu yaradılmadı (ffmpeg)")
    tmp.rename(dst)
    return {"frames": n, "touched": touched, "size": [W, H]}


def still(src: Path, ts: float, effects: list[dict[str, Any]], tl: float, w: int = 360, model: str = "accurate") -> np.ndarray:
    """Önizləmə: mənbə vaxtı ts-dəki kadra, zaman xəttində tl anı kimi, effektlər (tam emalla eyni funksiyalar)."""
    from montaj import background

    info = background.probe(src)
    W, H = info["w"] // 2 * 2, info["h"] // 2 * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", str(src), "-frames:v", "1", "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    f8 = np.frombuffer(raw[: W * H * 3], np.uint8).reshape(H, W, 3)
    sw = 540 if W <= H else 960
    sh = int(round(sw * H / W / 2) * 2)
    seg = background.Segmenter(model)
    try:
        ms = background.refine(seg.person(cv2.resize(f8, (sw, sh), interpolation=cv2.INTER_AREA)), None, 0)
    finally:
        seg.close()
    out = apply_frame(f8, matte(f8, ms), effects, [tl], [{} for _ in effects])
    return cv2.resize(out, (w, int(round(w * H / W))), interpolation=cv2.INTER_AREA)
