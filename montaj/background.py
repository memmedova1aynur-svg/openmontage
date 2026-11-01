"""Arxa fonun dəyişdirilməsi (yerli, pulsuz: MediaPipe insan seqmentasiyası).

Rejimlər (spec["mode"]):
  blur   — fon bulanır (portret effekti; ən etibarlısı), "strength" 5–60
  color  — tək rəng və ya qradiyent: "color", "color2" (yoxdursa tək rəng), "direction": "vertical" | "horizontal" | "radial"
  image  — şəkil (cover kimi doldurulur): "file"
  video  — video fon (dövrə ilə təkrarlanır): "file"
  scene  — Claude-un səhnəsi (sceneclip): "kind", "props" → video fon kimi
Ümumi seçimlər: "dim" 0..0.8 (fonu qaraltmaq), "keepBelow" 0..1 (bu hündürlükdən aşağı orijinal qalır — masa, əllər
havada qalmasın), "feather" (kənar yumşaltma, px), "smooth" 0..0.9 (kadrlar arası titrəməni azaltmaq), "model":
"accurate" (çoxsinifli, dəqiq) | "fast".

Nəticə — orijinalın yanında törəmə video (media/derived/), eyni ölçü, fps və kadr sayı; orijinal dəyişmir, səs orijinaldan.
Etik qayda: ekspertin olmadığı real məkanı (başqa ofis, ölkə) həqiqi kimi göstərmə — brend rəngi, qrafika, bulanıq fon normaldır.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Iterator

import numpy as np
from PIL import Image, ImageFilter

MODELS = {
    "accurate": ("selfie_multiclass.tflite",
                 "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"),
    "fast": ("selfie_segmenter.tflite",
             "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"),
}
DEFAULTS = {"strength": 22, "dim": 0.0, "keepBelow": None, "feather": 3, "smooth": 0.45, "model": "accurate", "direction": "vertical"}


def model_path(kind: str = "accurate") -> Path:
    from montaj.reframe import models_dir

    name, url = MODELS[kind]
    p = models_dir() / name
    if not p.is_file():
        tmp = p.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(p)
    return p


def _hex(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def normalize(spec: dict[str, Any]) -> dict[str, Any]:
    s = {**DEFAULTS, **{k: v for k, v in spec.items() if v is not None}}
    if s.get("mode") not in ("blur", "color", "image", "video", "scene"):
        raise ValueError(f"naməlum fon rejimi: {s.get('mode')} (blur, color, image, video, scene)")
    if s["mode"] == "color" and not s.get("color"):
        raise ValueError("rəng fonu üçün color lazımdır (məs. #C9577D)")
    if s["mode"] in ("image", "video") and not (s.get("file") and Path(s["file"]).is_file()):
        raise ValueError(f"fon faylı tapılmadı: {s.get('file')}")
    s["dim"] = float(min(0.8, max(0.0, s["dim"])))
    s["smooth"] = float(min(0.9, max(0.0, s["smooth"])))
    return s


def spec_key(spec: dict[str, Any], src: Path) -> str:
    """Eyni mənbə + eyni seçim → eyni törəmə fayl (keş)."""
    h = hashlib.sha1(json.dumps({**spec, "file": spec.get("file") and _file_sig(Path(spec["file"]))}, sort_keys=True).encode())
    h.update(_file_sig(src).encode())
    return h.hexdigest()[:10]


def _file_sig(p: Path) -> str:
    st = p.stat()
    return f"{p.name}:{st.st_size}:{int(st.st_mtime)}"


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
    """Kənarı dəqiqləşdirir (yumşaq hədd) və kadrlar arası titrəməni azaldır (yalnız kənar zonasında hamarlama)."""
    m = np.clip((mask - 0.25) / 0.5, 0, 1)
    # kiçik/nazik ləkələr (fondakı bitki, kölgə) çıxır: açma (erosion → dilation) yalnız "əsas gövdə" maskası üçün,
    # yumşaq kənarlar orijinal maskadan qalır
    h0, w0 = m.shape
    im = Image.fromarray((m > 0.5).astype(np.uint8) * 255).resize((max(8, w0 // 4), max(8, h0 // 4)), Image.BILINEAR)
    core = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(7)).resize((w0, h0), Image.BILINEAR)
    m = m * (np.asarray(core, dtype=np.float32) / 255.0)
    if prev is not None and smooth > 0:
        edge = (m > 0.02) & (m < 0.98) | (np.abs(m - prev) < 0.5)  # böyük hərəkətdə gecikmə olmasın
        m = np.where(edge, (1 - smooth) * m + smooth * prev, m)
    return m.astype(np.float32)


def _resize_mask(m: np.ndarray, w: int, h: int, feather: float) -> np.ndarray:
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    if feather and feather > 0:
        im = im.filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(im, dtype=np.float32)[..., None] / 255.0


def _cover(img: Image.Image, w: int, h: int) -> np.ndarray:
    sw, sh = img.size
    k = max(w / sw, h / sh)
    im = img.convert("RGB").resize((max(w, int(round(sw * k))), max(h, int(round(sh * k)))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return np.asarray(im.crop((x, y, x + w, y + h)), dtype=np.float32)


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


def _frames(src: Path, w: int, h: int, fps: str | None = None, loop: bool = False) -> Iterator[np.ndarray]:
    while True:
        cmd = ["ffmpeg", "-v", "error", "-i", str(src), "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
               + (f",fps={fps}" if fps else ""), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
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


class Backdrop:
    """Fon kadrı mənbəyi (rejimə görə)."""

    def __init__(self, spec: dict[str, Any], w: int, h: int, fps: str, scene_file: Path | None = None):
        self.spec, self.w, self.h = spec, w, h
        self.static = None
        self.it = None
        mode = spec["mode"]
        if mode == "color":
            self.static = _gradient(spec, w, h)
        elif mode == "image":
            self.static = _cover(Image.open(spec["file"]), w, h)
        elif mode in ("video", "scene"):
            self.it = _frames(Path(scene_file or spec["file"]), w, h, fps, loop=True)

    def frame(self, rgb: np.ndarray) -> np.ndarray:
        if self.spec["mode"] == "blur":
            r = max(2.0, float(self.spec.get("strength", 22)) / 4)
            small = Image.fromarray(rgb).resize((max(8, self.w // 4), max(8, self.h // 4)), Image.BILINEAR)
            bg = np.asarray(small.filter(ImageFilter.GaussianBlur(r)).resize((self.w, self.h), Image.BILINEAR), dtype=np.float32)
        elif self.static is not None:
            bg = self.static
        else:
            bg = next(self.it).astype(np.float32)
        if self.spec.get("dim"):
            bg = bg * (1 - self.spec["dim"])
        if bg is self.static or self.static is not None:
            if getattr(self, "_s16", None) is None:
                self._s16 = np.clip(bg, 0, 255).astype(np.uint16)
            return self._s16
        return np.clip(bg, 0, 255).astype(np.uint16)


def keep_mask(h: int, w: int, keep_below: float | None) -> np.ndarray | None:
    if keep_below is None:
        return None
    y = np.linspace(0, 1, h)[:, None, None]
    return np.clip((y - float(keep_below)) / 0.03, 0, 1).astype(np.float32) * np.ones((1, w, 1), np.float32)


def composite(rgb: np.ndarray, person: np.ndarray, bg: np.ndarray, keep: np.ndarray | None) -> np.ndarray:
    """Tam ədəd hesabı (uint16) — 1080x1920 kadrda float-dan ~5 dəfə tez."""
    a = person if keep is None else np.maximum(person, keep)
    a8 = (a * 255 + 0.5).astype(np.uint16)
    fg = rgb.astype(np.uint16)
    b16 = bg.astype(np.uint16) if bg.dtype != np.uint16 else bg
    return ((fg * a8 + b16 * (255 - a8) + 127) // 255).astype(np.uint8)


def probe(src: Path) -> dict[str, Any]:
    js = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height,avg_frame_rate,nb_frames:stream_side_data=rotation", "-of", "json", str(src)],
                                   capture_output=True, text=True, check=True).stdout)["streams"][0]
    w, h = int(js["width"]), int(js["height"])
    rot = 0
    for sd in js.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if abs(rot) in (90, 270):
        w, h = h, w
    return {"w": w, "h": h, "fps": js.get("avg_frame_rate") or "30/1"}


def _bg_input(spec: dict[str, Any], src: Path, w: int, h: int, fps: str, tmpdir: Path, scene_file: Path | None) -> tuple[list[str], str]:
    """ffmpeg üçün fon girişi və filtr zənciri ([1:v] → [bg])."""
    mode = spec["mode"]
    fit = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    if mode in ("color", "image"):
        img = Image.fromarray(np.clip(_gradient(spec, w, h), 0, 255).astype(np.uint8)) if mode == "color" else Image.open(spec["file"]).convert("RGB")
        f = tmpdir / f"bg_{mode}.png"
        img.save(f)
        args, chain = ["-loop", "1", "-framerate", fps, "-i", str(f)], f"[1:v]{fit},fps={fps}"
    elif mode in ("video", "scene"):
        args, chain = ["-stream_loop", "-1", "-i", str(scene_file or spec["file"])], f"[1:v]fps={fps},{fit}"
    else:  # blur — orijinalın özü kiçildilib bulandırılır
        r = max(2.0, float(spec.get("strength", 22)) / 4)
        args = ["-i", str(src)]
        chain = f"[1:v]fps={fps},scale={max(8, w // 4) // 2 * 2}:{max(8, h // 4) // 2 * 2},gblur=sigma={r:.1f},scale={w}:{h},setsar=1"
    d = float(spec.get("dim") or 0)
    if d:
        chain += f",colorchannelmixer=rr={1 - d:.3f}:gg={1 - d:.3f}:bb={1 - d:.3f}"
    return args, chain + ",setpts=PTS-STARTPTS,format=rgba[bg]"


def process(src: Path, dst: Path, spec: dict[str, Any], scene_file: Path | None = None,
            progress=lambda x: None, max_frames: int | None = None) -> dict[str, Any]:
    """Bütün videonu emal edir → dst (H.264, yüksək keyfiyyət, səssiz). Python yalnız maskanı hazırlayır (model + təmizləmə +
    kadrlar arası hamarlama); birləşdirmə və kodlaşdırma ffmpeg-dədir (sürət). Kənar titrəməsi ölçülür."""
    import tempfile

    info = probe(src)
    w, h, fps = info["w"] // 2 * 2, info["h"] // 2 * 2, info["fps"]
    sw = 540 if w <= h else 960  # model və maska üçün kiçik nüsxə
    sh = int(round(sw * h / w / 2) * 2)
    seg = Segmenter(spec.get("model", "accurate"))
    keep = keep_mask(sh, sw, spec.get("keepBelow"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".part.mp4")
    feather = max(0.5, float(spec.get("feather", 3)) * sw / 1080)
    prev, n, flick = None, 0, []
    with tempfile.TemporaryDirectory() as td:
        bg_args, bg_chain = _bg_input(spec, src, w, h, fps, Path(td), scene_file)
        graph = (f"[0:v]fps={fps},scale={w}:{h},setsar=1,setpts=PTS-STARTPTS,format=rgba[fg0];"
                 f"[2:v]setpts=PTS-STARTPTS,gblur=sigma={feather:.2f},scale={w}:{h}:flags=bilinear,format=gray[m];"
                 f"[fg0][m]alphamerge[fg];{bg_chain};[bg][fg]overlay=shortest=1:format=auto,format=yuv420p[v]")
        wr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-i", str(src), *bg_args,
                               "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{sw}x{sh}", "-r", fps, "-i", "-",
                               "-filter_complex", graph, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                               "-r", fps, str(tmp)], stdin=subprocess.PIPE)
        try:
            for small in _frames(src, sw, sh, fps):  # sabit fps — törəmə videonun vaxtı orijinalla eyni
                m = refine(seg.person(small), prev, spec.get("smooth", 0.45))
                if prev is not None:
                    band = (m > 0.05) & (m < 0.95)
                    flick.append(float(np.abs(m - prev)[band].mean()) if band.any() else 0.0)
                prev = m
                out = m if keep is None else np.maximum(m, keep[..., 0])
                wr.stdin.write((out * 255 + 0.5).astype(np.uint8).tobytes())
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


def still(src: Path, t: float, spec: dict[str, Any] | None, w: int = 360, scene_file: Path | None = None) -> np.ndarray:
    """Tək kadr önizləməsi (spec None → orijinal)."""
    info = probe(src)
    h = int(round(w * info["h"] / info["w"] / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", f"scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    rgb = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    if spec is None:
        return rgb
    seg = Segmenter(spec.get("model", "accurate"))
    try:
        m = refine(seg.person(rgb), None, 0)
    finally:
        seg.close()
    bd = Backdrop(spec, w, h, info["fps"], scene_file)
    return composite(rgb, _resize_mask(m, w, h, max(1.0, spec.get("feather", 3) * w / 1080)), bd.frame(rgb), keep_mask(h, w, spec.get("keepBelow")))
