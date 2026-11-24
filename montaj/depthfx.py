"""Dərinlik effektləri (Premiere / CapCut tərzi) — insan maskası üzərində, yerli və pulsuz (MediaPipe + OpenCV).

Hər effekt montajın ZAMAN XƏTTİNDƏ bir pəncərədir: {"type", "start", "dur", ...}. Yalnız pəncərə daxilindəki kadrlar
emal olunur; nəticə törəmə videodur (orijinal və fon törəməsi dəyişmir), render onu avtomatik götürür.

Növlər:
  behind   — yazı İNSANIN ARXASINDA: böyük başlıq fonda, baş/çiyin hərflərin önündə.
             text, size (eni payı, 0.2), y (mərkəz, hündürlük payı, 0.3), color, style solid|outline, upper,
             anim rise|scale|slide|fade
  text3d   — 3D yazı: qalınlıq (extrusion), işıq, perspektivdə fırlanma. text, size, y, color, side (yan rəng), depth,
             anim swing|fly|tilt, behind (true — insanın arxasında)
  sticker  — stiker kəsik: insanın ətrafında kontur + kölgə, fon dəyişir. outline (eni payı), outlineColor,
             bg dim|color|blur|keep, bgColor, dim
  focus    — yalnız FONA effekt (diqqət anı), insan toxunulmaz: bg dim|blur|gray|color|image, amount, color, file
  parallax — 2.5D kamera: insan və fon ayrı təbəqə, fərqli sürətlə yaxınlaşır. zoom (insan), bgZoom, drift
  popout   — çərçivədən çıxmaq: video kartın içinə kiçilir, baş kartın üst kənarından çölə çıxır.
             scale, cardTop ("auto" — başın hündürlüyünə görə; və ya 0..0.45), radius, color, color2
Ümumi: fadeIn, fadeOut (s).
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

TYPES = ("behind", "text3d", "sticker", "focus", "parallax", "popout")
COMMON = {"fadeIn": 0.35, "fadeOut": 0.35}
DEFAULTS: dict[str, dict[str, Any]] = {
    "behind": {"size": 0.2, "y": 0.3, "style": "solid", "upper": True, "anim": "rise", "font": "Montserrat", "weight": 800,
               "maxWidth": 0.94, "tracking": 0.0},
    "text3d": {"size": 0.21, "y": 0.28, "anim": "swing", "behind": True, "depth": 0.03, "font": "Montserrat", "weight": 800,
               "upper": True, "maxWidth": 0.9},
    "sticker": {"outline": 0.012, "outlineColor": "#FFFFFF", "bg": "dim", "dim": 0.6, "shadow": True},
    "focus": {"bg": "dim", "amount": 0.6},
    "parallax": {"zoom": 0.09, "bgZoom": 0.02, "drift": 0.015, "fadeOut": 0.7},
    "popout": {"scale": 0.8, "cardTop": "auto", "radius": 0.045, "shadow": True, "fadeIn": 0.5, "fadeOut": 0.5},
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
    if t == "sticker":
        s.setdefault("bgColor", deep)
    if t == "focus" and s["bg"] == "color":
        s.setdefault("color", deep)
    if t == "focus" and s["bg"] == "image" and not (s.get("file") and Path(s["file"]).is_file()):
        raise ValueError(f"focus image üçün fayl tapılmadı: {s.get('file')}")
    if t == "popout":
        s.setdefault("color", primary)
        s.setdefault("color2", deep)
    fi, fo = float(s["fadeIn"]), float(s["fadeOut"])
    s["fadeIn"], s["fadeOut"] = min(fi, s["dur"] / 2), min(fo, s["dur"] / 2)
    return s


def effects_key(effects: list[dict[str, Any]], src: Path) -> str:
    st = src.stat()
    h = hashlib.sha1(json.dumps(effects, sort_keys=True, ensure_ascii=False).encode())
    h.update(f"{src.name}:{st.st_size}:{int(st.st_mtime)}".encode())
    return h.hexdigest()[:10]


# ---------------------------------------------------------------------------
# Vaxt: mənbə kadrı → zaman xətti (eyni media bir neçə klipdə ola bilər)
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
# Yazı spraytları
# ---------------------------------------------------------------------------

def az_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def _rgb(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _font(e: dict[str, Any], px: int) -> ImageFont.FreeTypeFont:
    from montaj import fonts

    path = fonts.ttf_path(e.get("font"), e.get("weight")) or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(path, px)


def _measure(lines: list[str], font: ImageFont.FreeTypeFont, gap: float) -> tuple[int, int, list[tuple[int, int, int]]]:
    boxes = [font.getbbox(ln or " ") for ln in lines]
    lh = int(font.size * (1 + gap))
    w = max(b[2] - b[0] for b in boxes)
    return w, lh * (len(lines) - 1) + (boxes[-1][3]), [(b[0], b[2] - b[0], i * lh) for i, b in enumerate(boxes)]


def text_sprite(e: dict[str, Any], W: int) -> Image.Image:
    """Düz yazı (solid və ya kontur) — şəffaf RGBA, eni kadra sığışdırılır."""
    text = az_upper(e["text"]) if e.get("upper") else e["text"]
    lines = text.split("\n")
    px = max(12, int(W * float(e["size"])))
    while True:
        font = _font(e, px)
        tw, th, rows = _measure(lines, font, -0.08)
        if tw <= W * float(e.get("maxWidth", 0.94)) or px <= 14:
            break
        px = int(px * 0.94)
    stroke = max(2, int(px * 0.035)) if e.get("style") == "outline" else 0
    pad = stroke + 4
    im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = _rgb(e["color"])
    for (x0, lw, y), ln in zip(rows, lines):
        x = pad + (tw - lw) / 2 - x0
        if stroke:
            d.text((x, pad + y), ln, font=font, fill=(0, 0, 0, 0), stroke_width=stroke, stroke_fill=col + (255,))
        else:
            d.text((x, pad + y), ln, font=font, fill=col + (255,))
    return im


def extruded_sprite(e: dict[str, Any], W: int) -> tuple[np.ndarray, tuple[int, int]]:
    """3D yazı: arxa təbəqələr (yan üz, dərinə doğru tündləşir) + ön üz (yuxarıdan işıq). RGBA float32 0..1
    və ön üzün sprayt içindəki ofseti."""
    flat = text_sprite({**e, "style": "solid"}, W)
    fw, fh = flat.size
    depth = max(3, int(W * float(e["depth"])))
    dx, dy = 0.55, 0.85  # ekstruziya istiqaməti (aşağı-sağa)
    ox, oy = int(depth * dx) + 2, int(depth * dy) + 2
    out = np.zeros((fh + oy + 2, fw + ox + 2, 4), np.float32)
    a = np.asarray(flat, dtype=np.float32)[..., 3] / 255.0
    side = np.array(_rgb(e["side"]), np.float32) / 255.0
    for k in range(depth, 0, -1):
        x, y = int(round(k * dx)), int(round(k * dy))
        shade = 0.55 + 0.45 * (1 - k / depth)  # dərinə doğru tündləşir
        reg = out[y:y + fh, x:x + fw]
        reg[..., :3] = reg[..., :3] * (1 - a[..., None]) + side * shade * a[..., None]
        reg[..., 3] = np.maximum(reg[..., 3], a)
    front = np.array(_rgb(e["color"]), np.float32) / 255.0
    grad = np.linspace(1.18, 0.86, fh, dtype=np.float32)[:, None, None]  # yuxarıdan işıq
    face = np.clip(front * grad, 0, 1)
    # ön üzün kənarında incə işıq xətti (bevel təəssüratı)
    er = cv2.erode((a > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=max(1, fh // 120))
    rim = np.clip(a - er.astype(np.float32), 0, 1)[..., None]
    face = np.clip(face * (1 - rim * 0.35) + rim * 0.35, 0, 1)
    reg = out[0:fh, 0:fw]
    reg[..., :3] = reg[..., :3] * (1 - a[..., None]) + face * a[..., None]
    reg[..., 3] = np.maximum(reg[..., 3], a)
    return out, (fw, fh)


# ---------------------------------------------------------------------------
# Kompozisiya köməkçiləri (float32, 0..1)
# ---------------------------------------------------------------------------

def _paste(canvas_rgb: np.ndarray, canvas_a: np.ndarray, spr: np.ndarray, x: int, y: int) -> None:
    """RGBA sprayt (float) → (rgb, alfa) təbəqəsinə, kənardan çıxanı kəsir."""
    H, W = canvas_a.shape
    sh, sw = spr.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + sw), min(H, y + sh)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4]
    canvas_rgb[y0:y1, x0:x1] = canvas_rgb[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a
    canvas_a[y0:y1, x0:x1] = np.maximum(canvas_a[y0:y1, x0:x1], a[..., 0])


def _hex01(c: str) -> np.ndarray:
    return np.array(_rgb(c), np.float32) / 255.0


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
        return np.broadcast_to(_hex01(e.get("color") or e.get("bgColor") or "#222222"), f.shape)
    if kind == "image":
        if "img" not in cache:
            cache["img"] = _cover(Image.open(e["file"]), W, H)
        return cache["img"]
    return f


# ---------------------------------------------------------------------------
# Effektlər (kadr, maska, effekt, yerli vaxt, zərf) → kadr
# ---------------------------------------------------------------------------

def fx_behind(f, m, e, lt, env, cache):
    H, W = m.shape
    if "spr" not in cache:
        cache["spr"] = np.asarray(text_sprite(e, W), np.float32) / 255.0
    spr = cache["spr"]
    k = _ease_out(lt / 0.7)
    anim = e.get("anim", "rise")
    sc = 0.82 + 0.18 * _ease_back(lt / 0.6) if anim == "scale" else 1.0
    s = spr if abs(sc - 1) < 1e-3 else cv2.resize(spr, (max(2, int(spr.shape[1] * sc)), max(2, int(spr.shape[0] * sc))))
    x = (W - s.shape[1]) // 2 + (int(-W * 0.35 * (1 - k)) if anim == "slide" else 0)
    y = int(H * float(e["y"]) - s.shape[0] / 2) + (int(H * 0.05 * (1 - k)) if anim == "rise" else 0)
    rgb, a = np.zeros_like(f), np.zeros(m.shape, np.float32)
    _paste(rgb, a, s, x, y)
    a = a * env * (1 - m)
    return f * (1 - a[..., None]) + rgb * a[..., None]


def _perspective(spr: np.ndarray, ry: float, rx: float, scale: float) -> tuple[np.ndarray, np.ndarray]:
    """Sprayt düzbucaqlısını 3D-də fırladıb proyeksiya edir: (homoqrafiya, çıxış künclərinin mərkəzə nisbəti)."""
    h, w = spr.shape[:2]
    f = 2.4 * max(w, h)
    pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        X, Z = x * math.cos(ry), x * math.sin(ry)
        Y, Z = y * math.cos(rx) - Z * math.sin(rx), y * math.sin(rx) + Z * math.cos(rx)
        pts.append((X * f / (f + Z) * scale, Y * f / (f + Z) * scale))
    return np.float32([(0, 0), (w, 0), (w, h), (0, h)]), np.float32(pts)


def fx_text3d(f, m, e, lt, env, cache):
    H, W = m.shape
    if "spr" not in cache:
        cache["spr"], _ = extruded_sprite(e, W)
    spr = cache["spr"]
    anim = e.get("anim", "swing")
    t_in = lt / 0.9
    if anim == "fly":
        ry, rx, sc = 0.15 * math.sin(lt * 1.3), math.radians(55) * (1 - _ease_out(t_in)), 0.35 + 0.65 * _ease_back(t_in, 1.2)
    elif anim == "tilt":
        ry, rx, sc = math.radians(-16) + 0.12 * math.sin(lt * 0.9), math.radians(8), 1.0
    else:  # swing
        ry = math.radians(75) * (1 - _ease_back(t_in, 1.4)) + math.radians(7) * math.sin(lt * 1.4) * _sm(t_in)
        rx, sc = math.radians(6) * math.sin(lt * 0.8), 0.7 + 0.3 * _ease_out(t_in)
    src, dst = _perspective(spr, ry, rx, sc)
    cx, cy = W / 2, H * float(e["y"])
    M = cv2.getPerspectiveTransform(src, dst + np.float32([cx, cy]))
    warped = cv2.warpPerspective(spr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = warped[..., 3] * env
    # yumşaq kölgə yazının altında (yerə "basır")
    sh = cv2.GaussianBlur(warped[..., 3], (0, 0), W * 0.012)
    sh = _shift(sh, int(W * 0.012), int(W * 0.006)) * 0.35 * env
    if e.get("behind", True):
        a, sh = a * (1 - m), sh * (1 - m)
    out = f * (1 - sh[..., None])
    return out * (1 - a[..., None]) + warped[..., :3] * a[..., None]


def _shift(a: np.ndarray, dy: int, dx: int = 0) -> np.ndarray:
    """Təbəqəni sürüşdürür (np.roll kimi, amma kənar o biri tərəfə keçmir)."""
    H, W = a.shape[:2]
    return cv2.warpAffine(a, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def _dilate(m: np.ndarray, r: int) -> np.ndarray:
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    d = cv2.dilate((m > 0.5).astype(np.uint8), k)
    return cv2.GaussianBlur(d.astype(np.float32), (0, 0), max(1.0, r * 0.12))


def fx_sticker(f, m, e, lt, env, cache):
    H, W = m.shape
    r = max(2, int(W * float(e["outline"]) * _ease_back(lt / 0.45, 2.0)))
    d = np.clip(_dilate(m, r), 0, 1)
    d = np.maximum(d, m)
    cache["mask"] = d
    bg = _bg_variant(f, e.get("bg", "dim"), {**e, "color": e.get("bgColor")}, cache, float(e.get("dim", 0.6)))
    out = bg.copy()
    if e.get("shadow", True):
        sh = cv2.GaussianBlur(d, (0, 0), W * 0.018)
        sh = _shift(sh, int(W * 0.02)) * 0.45
        out = out * (1 - sh[..., None])
    oc = _hex01(e.get("outlineColor", "#FFFFFF"))
    out = out * (1 - d[..., None]) + oc * d[..., None]
    out = out * (1 - m[..., None]) + f * m[..., None]
    return f * (1 - env) + out * env


def fx_focus(f, m, e, lt, env, cache):
    cache["mask"] = m
    bg = _bg_variant(f, e.get("bg", "dim"), e, cache, float(e.get("amount", 0.6)))
    out = bg * (1 - m[..., None]) + f * m[..., None]
    return f * (1 - env) + out * env


def _fill_behind(f: np.ndarray, m: np.ndarray) -> np.ndarray:
    """İnsanın arxasındakı fonu təxmini bərpa edir (inpaint, kiçik ölçüdə) — 2.5D-də boşluq görünməsin."""
    H, W = m.shape
    sw, sh = max(16, W // 4), max(16, H // 4)
    small = (cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)
    hole = cv2.dilate((cv2.resize(m, (sw, sh)) > 0.2).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    fill = cv2.inpaint(small, hole, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
    fill = cv2.resize(cv2.GaussianBlur(fill, (0, 0), 2), (W, H), interpolation=cv2.INTER_LINEAR)
    md = cv2.GaussianBlur(cv2.resize(hole.astype(np.float32) / 255.0, (W, H)), (0, 0), 6)[..., None]
    return f * (1 - md) + fill * md


def _scale_about(img: np.ndarray, s: float, cx: float, cy: float, dx: float = 0.0) -> np.ndarray:
    M = np.float32([[s, 0, (1 - s) * cx + dx], [0, s, (1 - s) * cy]])
    H, W = img.shape[:2]
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_parallax(f, m, e, lt, env, cache):
    H, W = m.shape
    q = _ease_in_out(lt / e["dur"]) * env
    ys, xs = np.where(m > 0.5)
    cx, cy = (float(xs.mean()), float(ys.min() + (ys.max() - ys.min()) * 0.35)) if len(xs) else (W / 2, H * 0.4)
    bg = _scale_about(_fill_behind(f, m), 1 + float(e["bgZoom"]) * q, W / 2, H / 2, -W * float(e["drift"]) * q)
    s = 1 + float(e["zoom"]) * q
    fp, mp = _scale_about(f, s, cx, cy), _scale_about(m, s, cx, cy)
    return bg * (1 - mp[..., None]) + fp * mp[..., None]


def _round_mask(w: int, h: int, r: int) -> np.ndarray:
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return np.asarray(im, np.float32) / 255.0


def fx_popout(f, m, e, lt, env, cache):
    H, W = m.shape
    if "canvas" not in cache:
        c1, c2 = _hex01(e["color"]), _hex01(e["color2"])
        t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        cache["canvas"] = np.broadcast_to(c1 * (1 - t) + c2 * t, (H, W, 3)).astype(np.float32)
    k = _ease_in_out(env)
    s = 1 - (1 - float(e["scale"])) * k
    sw, sh = max(2, int(W * s)), max(2, int(H * s))
    x0, y0 = (W - sw) // 2, max(0, min(H - sh, int(H / 2 - sh / 2 + H * 0.04 * k)))  # kart bir az aşağıda: başa yer qalır
    fs = cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA)
    ms = cv2.resize(m, (sw, sh), interpolation=cv2.INTER_LINEAR)
    if "top" not in cache:  # başın yuxarısı (ilk kadrdan; sabit qalsın deyə keşlənir)
        rows = np.where((m > 0.5).mean(axis=1) > 0.01)[0]
        cache["top"] = rows[0] / H if len(rows) else 0.2
    ct = e["cardTop"]
    if ct == "auto":  # kartın üst kənarı alından/gözdən keçir — baş kartdan çölə çıxır
        ct = min(0.45, max(0.1, cache["top"] + 0.11))
    cut = int(sh * float(ct) * k)
    out = cache["canvas"].copy() * k + f * (1 - k)
    card = _round_mask(sw, sh - cut, max(1, int(W * float(e["radius"]) * k)))
    if e.get("shadow", True) and k > 0.01:
        shadow = np.zeros((H, W), np.float32)
        shadow[y0 + cut:y0 + sh, x0:x0 + sw] = card
        shadow = _shift(cv2.GaussianBlur(shadow, (0, 0), W * 0.02), int(W * 0.02)) * 0.4 * k
        out = out * (1 - shadow[..., None])
    reg = out[y0 + cut:y0 + sh, x0:x0 + sw]
    a = card[..., None]
    reg[:] = reg * (1 - a) + fs[cut:] * a
    # insan kartın kənarından çıxır (kəsilmədən üstə çəkilir)
    pa = ms[..., None]
    sub = out[y0:y0 + sh, x0:x0 + sw]
    sub[:] = sub * (1 - pa) + fs * pa
    return out


FX: dict[str, Callable] = {"behind": fx_behind, "text3d": fx_text3d, "sticker": fx_sticker, "focus": fx_focus,
                           "parallax": fx_parallax, "popout": fx_popout}
ORDER = {"focus": 0, "sticker": 1, "behind": 2, "text3d": 2, "parallax": 3, "popout": 4}  # fon → yazı → kamera → çərçivə


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
# Tam emal
# ---------------------------------------------------------------------------

def _up(m_small: np.ndarray, W: int, H: int) -> np.ndarray:
    m = cv2.resize(m_small, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(m, (0, 0), max(0.8, W / 900))


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
                f8 = apply_frame(f8, _up(ms, W, H), effects, tls, caches)
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
    out = apply_frame(f8, _up(ms, W, H), effects, [tl], [{} for _ in effects])
    return cv2.resize(out, (w, int(round(w * H / W))), interpolation=cv2.INTER_AREA)
