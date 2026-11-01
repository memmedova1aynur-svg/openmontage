"""Arxa fonun dəyişdirilməsi (yerli, pulsuz: MediaPipe insan seqmentasiyası) — dəyişdirildiyi hiss olunmasın.

Rejimlər (spec["mode"]):
  blur   — fon bulanır (portret effekti), "strength" 5–60
  color  — tək rəng və ya qradiyent: "color", "color2", "direction": "vertical" | "horizontal" | "radial"
  image  — şəkil: "file" və ya kitabxanadan "lib" (bg-lib); "bgZoom", "bgX", "bgY" — fonun yeri və miqyası
  video  — video fon (dövrə ilə): "file"
  scene  — Claude-un səhnəsi (sceneclip): "kind", "props"
Təbiilik (image / video / scene üçün standart açıqdır):
  "harmonize" — fonun parlaqlığı və rəng temperaturu orijinal otağın işığına yaxınlaşır (insanın üzünə toxunulmur)
  "focus"     — fonun kamera fokusu kimi yüngül bulanması (sigma, 1080 px üçün)
  "wrap"      — kənar işığı: fonun işığı insanın kənarına azca düşür (0..0.6)
  "grain"     — kameranın dənəvərliyi fona da ("auto" — orijinaldan ölçülür)
  "keepBelow" — "auto": masa avtomatik tapılır, masa və əllər orijinal qalır (oturan şəxs); və ya 0..1 / null
  "shadow"    — "auto": ayaqları görünən (ayaqüstə) şəxsin ayağı altında yumşaq kölgə
Ümumi: "dim" 0..0.8, "feather", "smooth" (titrəmə), "model" accurate | fast.

Nəticə — orijinalın yanında törəmə video (media/derived/), eyni ölçü, fps və kadr sayı; orijinal dəyişmir, səs orijinaldan.
Etik qayda: ekspertin olmadığı real məkanı (başqa ofis, ölkə) həqiqi kimi göstərmə — studiya/interyer fonu, brend rəngi,
qrafika, bulanıq fon normaldır.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Iterator

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MODELS = {
    "accurate": ("selfie_multiclass.tflite",
                 "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"),
    "fast": ("selfie_segmenter.tflite",
             "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"),
}
DEFAULTS = {"strength": 22, "dim": 0.0, "keepBelow": None, "feather": 3, "smooth": 0.45, "model": "accurate", "direction": "vertical",
            "bgZoom": 1.0, "bgX": 0.5, "bgY": 0.5}
NATURAL = {"harmonize": True, "focus": "auto", "wrap": 0.3, "grain": "auto", "keepBelow": "auto", "shadow": "auto"}


def model_path(kind: str = "accurate") -> Path:
    from montaj.reframe import models_dir

    name, url = MODELS[kind]
    p = models_dir() / name
    if not p.is_file():
        tmp = p.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(p)
    return p


# ---------------------------------------------------------------------------
# Fon kitabxanası
# ---------------------------------------------------------------------------

def lib_dir() -> Path:
    """Fon kitabxanası repoda (montaj/backgrounds) — hər sessiyada əlçatandır. Sınaq üçün MONTAJ_BG_DIR."""
    import os

    from montaj.config import REPO_ROOT

    d = Path(os.environ.get("MONTAJ_BG_DIR") or REPO_ROOT / "montaj" / "backgrounds")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _img_stats(img: Image.Image) -> dict[str, Any]:
    a = np.asarray(img.convert("RGB").resize((96, int(96 * img.height / img.width) or 96)), dtype=float)
    g = a.mean(axis=2)
    edges = float(np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean())
    return {"rgb": [round(float(x), 1) for x in a.reshape(-1, 3).mean(axis=0)], "bright": round(float(g.mean()), 1),
            "warm": round(float(a[..., 0].mean() - a[..., 2].mean()), 1), "busy": round(edges, 2),
            "w": img.width, "h": img.height}


def lib_load() -> dict[str, Any]:
    f = lib_dir() / "index.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def lib_add(files: list[Path], tags: list[str] | None = None) -> list[dict[str, Any]]:
    idx = lib_load()
    out = []
    for f in files:
        img = Image.open(f)
        h = hashlib.sha1(Path(f).read_bytes()).hexdigest()[:8]
        name = f"bg_{h}{Path(f).suffix.lower() or '.jpg'}"
        shutil.copyfile(f, lib_dir() / name)
        rec = {"id": h, "file": name, "source": Path(f).name, "tags": tags or [], **_img_stats(img)}
        idx[h] = rec
        out.append(rec)
    (lib_dir() / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def lib_file(ref: str) -> Path:
    idx = lib_load()
    rec = idx.get(ref) or next((r for r in idx.values() if r["source"] == ref or r["file"] == ref), None)
    if not rec:
        raise ValueError(f"kitabxanada fon tapılmadı: {ref}")
    return lib_dir() / rec["file"]


def lib_rank(an: dict[str, Any], top: int = 3, tags: list[str] | None = None) -> list[dict[str, Any]]:
    """Videonun orijinal otaq işığına ən yaxın fonlar: parlaqlıq, rəng temperaturu, şaquli format, duruşa uyğunluq
    (teq "ayaqüstə" / "oturan"); çox qarışıq fon cəzalanır."""
    old = an.get("oldbg") or {}
    ob, ow = float(old.get("bright", 128)), float(old.get("warm", 0))
    vertical = an.get("h", 16) >= an.get("w", 9)
    scored = []
    for r in lib_load().values():
        if tags and not set(tags) & set(r.get("tags") or []):
            continue
        s = -abs(r["bright"] - ob) / 35 - abs(r["warm"] - ow) / 30 - max(0.0, r["busy"] - 14) / 10
        if (r["h"] >= r["w"]) == vertical:
            s += 0.8
        want = {"standing": "ayaqüstə", "seated": "oturan", "half": "oturan"}.get(an.get("posture") or "")
        if want and want in (r.get("tags") or []):  # duruşa uyğun fon: ayaqüstəyə döşəməli, oturana divar/rəf
            s += 0.7
        scored.append({**r, "score": round(s, 2)})
    return sorted(scored, key=lambda r: -r["score"])[:top]


# ---------------------------------------------------------------------------
# Seçimlər
# ---------------------------------------------------------------------------

def _hex(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def normalize(spec: dict[str, Any]) -> dict[str, Any]:
    mode = spec.get("mode")
    if mode not in ("blur", "color", "image", "video", "scene"):
        raise ValueError(f"naməlum fon rejimi: {mode} (blur, color, image, video, scene)")
    base = {**DEFAULTS, **(NATURAL if mode in ("image", "video", "scene") else {})}
    s = {**base, **{k: v for k, v in spec.items() if v is not None}}
    if mode == "color" and not s.get("color"):
        raise ValueError("rəng fonu üçün color lazımdır (məs. #C9577D)")
    if mode == "image" and s.get("lib") and not s.get("file"):
        s["file"] = str(lib_file(s["lib"]))
    if mode in ("image", "video") and not (s.get("file") and Path(s["file"]).is_file()):
        raise ValueError(f"fon faylı tapılmadı: {s.get('file') or s.get('lib')}")
    s["dim"] = float(min(0.8, max(0.0, s["dim"])))
    s["smooth"] = float(min(0.9, max(0.0, s["smooth"])))
    s["wrap"] = float(min(0.6, max(0.0, s.get("wrap") or 0)))
    return s


def spec_key(spec: dict[str, Any], src: Path) -> str:
    """Eyni mənbə + eyni seçim → eyni törəmə fayl (keş)."""
    h = hashlib.sha1(json.dumps({**spec, "file": spec.get("file") and _file_sig(Path(spec["file"]))}, sort_keys=True).encode())
    h.update(_file_sig(src).encode())
    return h.hexdigest()[:10]


def _file_sig(p: Path) -> str:
    st = p.stat()
    return f"{p.name}:{st.st_size}:{int(st.st_mtime)}"


# ---------------------------------------------------------------------------
# Seqmentasiya
# ---------------------------------------------------------------------------

class Segmenter:
    def __init__(self, kind: str = "accurate"):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self.mp, self.kind = mp, kind
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=str(model_path(kind))), output_confidence_masks=True))

    def person(self, rgb: np.ndarray) -> np.ndarray:
        r = self.seg.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
        cm = r.confidence_masks
        m = (1.0 - np.squeeze(cm[0].numpy_view())) if self.kind == "accurate" else np.squeeze(cm[0].numpy_view())
        return np.clip(m.astype(np.float32), 0, 1)

    def close(self) -> None:
        self.seg.close()


def refine(mask: np.ndarray, prev: np.ndarray | None, smooth: float) -> np.ndarray:
    """Kənarı dəqiqləşdirir (yumşaq hədd), kiçik ləkələri (fondakı bitki) çıxarır, kadrlar arası titrəməni azaldır."""
    m = np.clip((mask - 0.25) / 0.5, 0, 1)
    h0, w0 = m.shape
    im = Image.fromarray((m > 0.5).astype(np.uint8) * 255).resize((max(8, w0 // 4), max(8, h0 // 4)), Image.BILINEAR)
    core = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(7)).resize((w0, h0), Image.BILINEAR)
    m = m * (np.asarray(core, dtype=np.float32) / 255.0)
    if prev is not None and smooth > 0:
        edge = (m > 0.02) & (m < 0.98) | (np.abs(m - prev) < 0.5)  # böyük hərəkətdə gecikmə olmasın
        m = np.where(edge, (1 - smooth) * m + smooth * prev, m)
    return m.astype(np.float32)


def _gradient(spec: dict[str, Any], w: int, h: int) -> np.ndarray:
    c1 = _hex(spec["color"])
    c2 = _hex(spec.get("color2") or spec["color"])
    d = spec.get("direction", "vertical")
    if d == "horizontal":
        t = np.linspace(0, 1, w)[None, :, None]
    elif d == "radial":
        yy, xx = np.mgrid[0:h, 0:w]
        t = np.clip(np.hypot((xx - w / 2) / (w / 2), (yy - h * 0.4) / (h / 2)) / 1.2, 0, 1)[..., None]
    else:
        t = np.linspace(0, 1, h)[:, None, None]
    return np.broadcast_to(c1 * (1 - t) + c2 * t, (h, w, 3)).astype(np.float32)


def keep_mask(h: int, w: int, keep_below: float | None) -> np.ndarray | None:
    if keep_below is None:
        return None
    y = np.linspace(0, 1, h)[:, None, None]
    return np.clip((y - float(keep_below)) / 0.02, 0, 1).astype(np.float32) * np.ones((1, w, 1), np.float32)


def composite(rgb: np.ndarray, person: np.ndarray, bg: np.ndarray, keep: np.ndarray | None) -> np.ndarray:
    """Sadə birləşdirmə (tam ədəd hesabı) — yoxlama və köməkçi istifadə üçün; tam emal ffmpeg-dədir."""
    a = person if keep is None else np.maximum(person, keep)
    a8 = (a * 255 + 0.5).astype(np.uint16)
    return ((rgb.astype(np.uint16) * a8 + bg.astype(np.uint16) * (255 - a8) + 127) // 255).astype(np.uint8)


def _frames(src: Path, w: int, h: int, fps: str | None = None, ss: float = 0.0, loop: bool = False) -> Iterator[np.ndarray]:
    while True:
        cmd = ["ffmpeg", "-v", "error", *(["-ss", f"{ss:.3f}"] if ss else []), "-i", str(src), "-vf",
               f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}" + (f",fps={fps}" if fps else ""),
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        n = w * h * 3
        got = False
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            got = True
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        p.stdout.close()
        p.wait()
        if not loop or not got:
            return


def probe(src: Path) -> dict[str, Any]:
    js = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height,avg_frame_rate:stream_side_data=rotation:format=duration", "-of", "json", str(src)],
                                   capture_output=True, text=True, check=True).stdout)
    st = js["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    rot = 0
    for sd in st.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if abs(rot) in (90, 270):
        w, h = h, w
    return {"w": w, "h": h, "fps": st.get("avg_frame_rate") or "30/1", "duration": float((js.get("format") or {}).get("duration") or 0)}


# ---------------------------------------------------------------------------
# Kadrın analizi (bir dəfə, keşlənir): otaq işığı, dənəvərlik, masa, ayaqlar
# ---------------------------------------------------------------------------

def _table_edge(gray: np.ndarray, mask: np.ndarray) -> tuple[float, float]:
    """Aşağı 45%-də insandan kənar sütunlarda ən güclü üfüqi kənar (masanın ön/üst xətti): (y payı, güc)."""
    h, w = gray.shape
    dy = np.abs(gray[2:] - gray[:-2])  # y-1..y+1
    free = (mask[1:-1] < 0.15)
    lo = int(h * 0.55)
    best, by = 0.0, None
    for y in range(lo, h - 3):
        cols = free[y]
        if cols.mean() < 0.12:
            continue
        v = float(dy[y][cols].mean()) * min(1.0, cols.mean() * 3)
        if v > best:
            best, by = v, y + 1
    return ((by / h) if by else 1.0), best


def analyze(src: Path, ranges: list[tuple[float, float]] | None = None, model: str = "accurate", n: int = 6) -> dict[str, Any]:
    info = probe(src)
    w = 360 if info["w"] <= info["h"] else 640
    h = int(round(w * info["h"] / info["w"] / 2) * 2)
    rs = ranges or [(0.0, info["duration"] or 1.0)]
    total = sum(b - a for a, b in rs)
    ts = []
    for k in range(n):
        x = total * (k + 0.5) / n
        for a, b in rs:
            if x <= b - a:
                ts.append(a + x)
                break
            x -= b - a
    seg = Segmenter(model)
    pers, olds, noise, tables, feet, boxes = [], [], [], [], [], []
    try:
        for t in ts:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", f"scale={w}:{h}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            if len(raw) < w * h * 3:
                continue
            rgb = np.frombuffer(raw[: w * h * 3], np.uint8).reshape(h, w, 3).astype(float)
            m = refine(seg.person(rgb.astype(np.uint8)), None, 0)
            p, b = m > 0.5, m < 0.1
            if p.any():
                pers.append(rgb[p].mean(axis=0))
            if b.any():
                olds.append(rgb[b].mean(axis=0))
            g = rgb.mean(axis=2)
            blur = np.asarray(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), dtype=float)
            if b.sum() > 100:
                noise.append(float((g - blur)[b].std()))
            tables.append(_table_edge(g, m))
            rows = np.where((m > 0.5).mean(axis=1) > 0.01)[0]
            if len(rows):
                feet.append(rows[-1] / h)
                cols = np.where((m > 0.5).any(axis=0))[0]
                boxes.append([cols[0] / w, rows[0] / h, cols[-1] / w, rows[-1] / h])
    finally:
        seg.close()

    def stats(arr):
        if not arr:
            return None
        c = np.mean(arr, axis=0)
        return {"rgb": [round(float(x), 1) for x in c], "bright": round(float(c.mean()), 1), "warm": round(float(c[0] - c[2]), 1)}
    ty = [y for y, s in tables if s > 6 and y < 0.985]
    table = round(float(np.median(ty)) - 0.004, 3) if len(ty) >= max(2, len(tables) // 2) and np.std(ty) < 0.03 else None
    fb = float(np.median(feet)) if feet else 1.0
    standing = fb < 0.965 and table is None
    return {"w": info["w"], "h": info["h"], "subject": stats(pers), "oldbg": stats(olds),
            "noise": round(float(np.median(noise)), 2) if noise else 0.0, "table": table, "feet": round(fb, 3),
            "posture": "standing" if standing else "seated" if table is not None else "half",
            "box": [round(float(x), 3) for x in np.median(boxes, axis=0)] if boxes else None}


def harmonize_gains(an: dict[str, Any], bg_rgb: list[float], k: float = 0.6) -> list[float]:
    """Yeni fonun kanal ortalamalarını orijinal otağınkına yaxınlaşdıran əmsallar (parlaqlıq + ağ balansı)."""
    old = (an.get("oldbg") or {}).get("rgb")
    if not old:
        return [1.0, 1.0, 1.0]
    return [round(float(np.clip((max(1.0, o) / max(1.0, n)) ** k, 0.6, 1.6)), 4) for o, n in zip(old, bg_rgb)]


def _bg_stats_of(spec: dict[str, Any], scene_file: Path | None, w: int, h: int) -> list[float]:
    if spec["mode"] == "image":
        return _img_stats(Image.open(spec["file"]))["rgb"]
    src = scene_file or Path(spec["file"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(src), "-frames:v", "1", "-vf", "scale=96:-2",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).astype(float)
    return [float(x) for x in a.reshape(-1, 3).mean(axis=0)] if a.size >= 3 else [128.0, 128.0, 128.0]


def resolve(spec: dict[str, Any], an: dict[str, Any], scene_file: Path | None = None) -> dict[str, Any]:
    """"auto" seçimləri analizlə konkret dəyərə çevirir (masa, kölgə, dənəvərlik, rəng uyğunlaşması)."""
    s = dict(spec)
    if s.get("keepBelow") == "auto":
        s["keepBelow"] = an.get("table")
    if s.get("shadow") == "auto":
        s["shadow"] = an.get("posture") == "standing"
    if s.get("grain") == "auto":
        s["grain"] = round(float(min(12.0, an.get("noise", 0) * 1.4)), 1)
    if s.get("focus") == "auto":  # detallı (qarışıq) fon daha çox bulanır — kamera insana fokuslanıb, fon arxada
        busy = _img_stats(Image.open(s["file"]))["busy"] if s["mode"] == "image" else 14.0
        s["focus"] = round(float(np.clip(1.5 + (busy - 8) * 0.25, 1.5, 6.0)), 2)
    if s.get("harmonize") and s["mode"] in ("image", "video", "scene"):
        s["gains"] = harmonize_gains(an, _bg_stats_of(s, scene_file, an["w"], an["h"]))
    return s


# ---------------------------------------------------------------------------
# Tam emal (maska Python-da, birləşdirmə ffmpeg-də)
# ---------------------------------------------------------------------------

def _bg_input(spec: dict[str, Any], src: Path, w: int, h: int, fps: str, tmpdir: Path, scene_file: Path | None,
              ss: float = 0.0, dur: float = 3600.0) -> tuple[list[str], str]:
    """ffmpeg üçün fon girişi və filtr zənciri ([1:v] → [bg])."""
    mode = spec["mode"]
    z = max(1.0, float(spec.get("bgZoom") or 1))
    fit = (f"scale={w}*{z:.3f}:{h}*{z:.3f}:force_original_aspect_ratio=increase,"
           f"crop={w}:{h}:(iw-{w})*{float(spec.get('bgX', 0.5)):.3f}:(ih-{h})*{float(spec.get('bgY', 0.5)):.3f},setsar=1")
    if mode in ("color", "image"):
        img = Image.fromarray(np.clip(_gradient(spec, w, h), 0, 255).astype(np.uint8)) if mode == "color" else Image.open(spec["file"]).convert("RGB")
        f = tmpdir / f"bg_{mode}.png"
        img.save(f)
        # -t: sonsuz dövrə filtr qrafında kadr yığmasın (yaddaş)
        args, chain = ["-loop", "1", "-framerate", fps, "-t", f"{dur:.3f}", "-i", str(f)], f"[1:v]{fit},fps={fps}"
    elif mode in ("video", "scene"):
        args, chain = ["-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", str(scene_file or spec["file"])], f"[1:v]fps={fps},{fit}"
    else:  # blur — orijinalın özü kiçildilib bulandırılır
        r = max(2.0, float(spec.get("strength", 22)) / 4)
        args = [*(["-ss", f"{ss:.3f}"] if ss else []), "-t", f"{dur:.3f}", "-i", str(src)]
        chain = f"[1:v]fps={fps},scale={max(8, w // 4) // 2 * 2}:{max(8, h // 4) // 2 * 2},gblur=sigma={r:.1f},scale={w}:{h},setsar=1"
    g = spec.get("gains")
    if g:
        chain += f",colorchannelmixer=rr={g[0]:.4f}:gg={g[1]:.4f}:bb={g[2]:.4f}"
    d = float(spec.get("dim") or 0)
    if d:
        chain += f",colorchannelmixer=rr={1 - d:.3f}:gg={1 - d:.3f}:bb={1 - d:.3f}"
    foc = (float(spec.get("focus") or 0) if not isinstance(spec.get("focus"), str) else 2.5) * w / 1080
    if foc > 0.2 and mode != "blur":
        chain += f",gblur=sigma={foc:.2f}"
    gr = float(spec.get("grain") or 0) if not isinstance(spec.get("grain"), str) else 0.0
    if gr > 0.3:
        chain += f",noise=alls={gr:.1f}:allf=t"
    return args, chain + ",setpts=PTS-STARTPTS,format=rgba[bg]"


def _shadow(m: np.ndarray, strength: float = 0.38) -> np.ndarray:
    """Ayaq altında yumşaq kölgə (ellips) — ayaqüstə şəxs yerdə "üzməsin"."""
    h, w = m.shape
    rows = np.where((m > 0.5).mean(axis=1) > 0.005)[0]
    out = np.zeros((h, w), np.float32)
    if not len(rows) or rows[-1] >= h - 2:
        return out
    yb = rows[-1]
    band = m[max(0, yb - int(h * 0.05)):yb + 1] > 0.5
    cols = np.where(band.any(axis=0))[0]
    if not len(cols):
        return out
    cx, half = (cols[0] + cols[-1]) / 2, max(6, (cols[-1] - cols[0]) * 0.8)
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).ellipse([cx - half, yb - h * 0.012, cx + half, yb + h * 0.018], fill=int(255 * strength))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(max(2, h * 0.012))), dtype=np.float32) / 255.0


def process(src: Path, dst: Path, spec: dict[str, Any], scene_file: Path | None = None,
            progress=lambda x: None, max_frames: int | None = None, ss: float = 0.0) -> dict[str, Any]:
    """Videonu emal edir → dst (H.264, yüksək keyfiyyət, səssiz). spec artıq `resolve` olunmuş olmalıdır.
    Python maskanı (və kölgəni) hazırlayır; birləşdirmə, kənar işığı, fokus, dənəvərlik və kodlaşdırma ffmpeg-dədir."""
    import tempfile

    info = probe(src)
    w, h, fps = info["w"] // 2 * 2, info["h"] // 2 * 2, info["fps"]
    sw = 540 if w <= h else 960
    sh = int(round(sw * h / w / 2) * 2)
    seg = Segmenter(spec.get("model", "accurate"))
    kb = spec.get("keepBelow")
    keep = keep_mask(sh, sw, kb if isinstance(kb, (int, float)) else None)
    shadow = bool(spec.get("shadow") is True)
    wrap = float(spec.get("wrap") or 0) if spec["mode"] != "blur" else 0.0
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".part.mp4")
    feather = max(0.5, float(spec.get("feather", 3)) * sw / 1080)
    prev, n, flick = None, 0, []
    mh = sh * 2 if shadow else sh
    with tempfile.TemporaryDirectory() as td:
        num, den = (fps.split("/") + ["1"])[:2]
        dur = (max_frames / (float(num) / float(den or 1)) if max_frames else max(0.1, info["duration"] - ss)) + 1.0
        bg_args, bg_chain = _bg_input(spec, src, w, h, fps, Path(td), scene_file, ss, dur)
        parts = [f"[0:v]fps={fps},scale={w}:{h},setsar=1,setpts=PTS-STARTPTS,format=rgba[fg0]"]
        if shadow:
            parts.append(f"[2:v]setpts=PTS-STARTPTS,split[mm][ss0];[mm]crop={sw}:{sh}:0:0[mraw];[ss0]crop={sw}:{sh}:0:{sh},"
                         f"scale={w}:{h}:flags=bilinear,format=gray[sa]")
        else:
            parts.append("[2:v]setpts=PTS-STARTPTS[mraw]")
        nsplit = 3 if wrap else 1
        parts.append(f"[mraw]gblur=sigma={feather:.2f},scale={w}:{h}:flags=bilinear,format=gray"
                     + (f",split={nsplit}[m][mw1][mw2]" if wrap else "[m]"))
        parts.append(bg_chain.replace("[bg]", "[bg0]"))
        cur = "bg0"
        if shadow:
            parts.append(f"[{cur}]split[bgA][bgB];[bgB]colorchannelmixer=rr=0:gg=0:bb=0[blk];[blk][sa]alphamerge[shL];"
                         f"[bgA][shL]overlay=shortest=1:format=auto[bgS]")
            cur = "bgS"
        if wrap:
            parts.append(f"[{cur}]split[bgx][bgw]")
            cur = "bgx"
        parts.append(f"[fg0][m]alphamerge[fg];[{cur}][fg]overlay=shortest=1:format=auto[comp]")
        out = "comp"
        if wrap:
            r = max(2.0, 12 * w / 1080)
            parts.append(f"[mw1]negate,gblur=sigma={r:.1f}[inv];[inv][mw2]blend=all_mode=multiply[wa];"
                         f"[bgw]gblur=sigma={r * 2:.1f}[bgw2];[bgw2][wa]alphamerge,colorchannelmixer=aa={wrap:.2f}[wl];"
                         f"[comp][wl]overlay=shortest=1:format=auto[comp2]")
            out = "comp2"
        parts.append(f"[{out}]format=yuv420p[v]")
        wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", *(["-ss", f"{ss:.3f}"] if ss else []), "-i", str(src), *bg_args,
                               "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{sw}x{mh}", "-r", fps, "-i", "-",
                               "-filter_complex", ";".join(parts), "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "medium",
                               "-crf", "14", "-r", fps, str(tmp)], stdin=subprocess.PIPE)
        try:
            for small in _frames(src, sw, sh, fps, ss):  # sabit fps — törəmə videonun vaxtı orijinalla eyni
                m = refine(seg.person(small), prev, spec.get("smooth", 0.45))
                if prev is not None:
                    band = (m > 0.05) & (m < 0.95)
                    flick.append(float(np.abs(m - prev)[band].mean()) if band.any() else 0.0)
                prev = m
                mo = m if keep is None else np.maximum(m, keep[..., 0])
                buf = (mo * 255 + 0.5).astype(np.uint8)
                if shadow:
                    buf = np.vstack([buf, (_shadow(m) * 255 + 0.5).astype(np.uint8)])
                wr.stdin.write(buf.tobytes())
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
        raise RuntimeError("arxa fon videosu yaradılmadı (ffmpeg)")
    tmp.rename(dst)
    return {"frames": n, "size": [w, h], "flicker": round(float(np.mean(flick)) if flick else 0.0, 4)}


def still(src: Path, t: float, spec: dict[str, Any] | None, w: int = 300, scene_file: Path | None = None) -> np.ndarray:
    """Tək kadr önizləməsi — tam emalla EYNİ yol (qısa parça emal olunur), spec None → orijinal."""
    import tempfile

    info = probe(src)
    h = int(round(w * info["h"] / info["w"] / 2) * 2)
    if spec is None:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", f"scale={w}:{h}",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "p.mp4"
        process(src, out, {**spec, "smooth": 0}, scene_file, max_frames=2, ss=t)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-vf", f"scale={w}:{h}",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)
