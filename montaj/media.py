"""Media köməkçiləri: ffprobe, önizləmə proksisi, dalğa forması, səssizlik."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def probe(path: Path) -> dict[str, Any]:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_streams", "-show_format", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(out.stdout)
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float((data.get("format") or {}).get("duration") or 0)
    if not dur:
        for s in (v, a):
            if s and s.get("duration"):
                dur = max(dur, float(s["duration"]))
    info: dict[str, Any] = {
        "duration": round(dur, 3),
        "hasVideo": v is not None,
        "hasAudio": a is not None,
    }
    if v is not None:
        w, h = int(v.get("width") or 0), int(v.get("height") or 0)
        rot = 0
        for sd in v.get("side_data_list") or []:
            if "rotation" in sd:
                rot = int(float(sd["rotation"]))
        if abs(rot) in (90, 270):
            w, h = h, w
        info["width"], info["height"] = w, h
        fr = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
        try:
            n, d = fr.split("/")
            info["fps"] = round(float(n) / float(d), 3) if float(d) else 0
        except ValueError:
            info["fps"] = 0
        info["videoCodec"] = v.get("codec_name")
        info["fpsRate"] = v.get("avg_frame_rate") or v.get("r_frame_rate")
        trc = v.get("color_transfer") or ""
        info["colorTransfer"] = trc or None
        info["colorPrimaries"] = v.get("color_primaries")
        info["hdr"] = trc in ("smpte2084", "arib-std-b67")
        pix = v.get("pix_fmt") or ""
        info["pixFmt"] = pix
        info["bitDepth"] = 10 if ("10" in pix or "p010" in pix) else 12 if "12" in pix else 8
        fmt_name = (data.get("format") or {}).get("format_name", "")
        is_still = (v.get("codec_name") in ("mjpeg", "png", "webp", "bmp", "tiff", "gif", "heic", "hevc")
                    and (fmt_name.endswith("_pipe") or fmt_name in ("image2", "png_pipe", "jpeg_pipe")
                         or (v.get("nb_frames") in ("1", None) and not dur)))
        if is_still and a is None and fmt_name not in ("mov,mp4,m4a,3gp,3g2,mj2", "matroska,webm"):
            info["isImage"] = True
            info["duration"] = 600.0  # hərəkətsiz şəkil istənilən müddətdə istifadə oluna bilər
            info["fps"] = 0
    if a is not None:
        info["audioCodec"] = a.get("codec_name")
    return info


def make_image_preview(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-frames:v", "1",
                    "-vf", "scale='min(1440,iw)':-2", "-q:v", "3", str(dst)], check=True, capture_output=True)


def make_proxy(src: Path, dst: Path, has_video: bool, has_audio: bool, hdr: bool = False) -> None:
    """Brauzerdə rahat oynayan H.264/AAC (və ya yalnız AAC) önizləmə nüsxəsi."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp" + dst.suffix)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src)]
    if hdr:
        tm = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
              "zscale=t=bt709:m=bt709:r=tv,")
    else:
        tm = ""
    if has_video:
        cmd += [
            "-map", "0:v:0", "-vf", tm + "scale='min(1280,iw)':-2,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-g", "15", "-movflags", "+faststart",
        ]
    else:
        cmd += ["-vn"]
    if has_audio:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "128k", "-ar", "48000"]
    else:
        cmd += ["-an"]
    cmd += ["-f", "mp4", str(tmp)]
    subprocess.run(cmd, check=True, capture_output=True)
    tmp.replace(dst)


def read_mono(src: Path, rate: int = 8000) -> np.ndarray:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:a:0", "-ac", "1",
         "-ar", str(rate), "-f", "s16le", "-"],
        capture_output=True, check=True,
    )
    return np.frombuffer(out.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def peaks(src: Path, per_second: int = 50) -> dict[str, Any]:
    rate = 8000
    pcm = read_mono(src, rate)
    hop = rate // per_second
    n = len(pcm) // hop
    if n == 0:
        return {"perSecond": per_second, "peaks": []}
    blocks = np.abs(pcm[: n * hop]).reshape(n, hop).max(axis=1)
    return {"perSecond": per_second, "peaks": [round(float(x), 3) for x in blocks]}


_SIL_START = re.compile(r"silence_start: (-?[\d.]+)")
_SIL_END = re.compile(r"silence_end: (-?[\d.]+)")


def detect_silence(src: Path, start: float, end: float, noise_db: float = -35.0,
                   min_silence: float = 0.6) -> list[tuple[float, float]]:
    """Mənbə faylının [start, end] aralığında səssiz hissələri qaytarır (mənbə vaxtı)."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
         "-i", str(src), "-map", "0:a:0", "-af",
         f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    res: list[tuple[float, float]] = []
    cur: float | None = None
    for line in proc.stderr.splitlines():
        m = _SIL_START.search(line)
        if m:
            cur = max(0.0, float(m.group(1)))
            continue
        m = _SIL_END.search(line)
        if m and cur is not None:
            res.append((start + cur, start + float(m.group(1))))
            cur = None
    if cur is not None:
        res.append((start + cur, end))
    return [(round(a, 3), round(min(b, end), 3)) for a, b in res if b > a]


def keep_ranges(start: float, end: float, remove: list[tuple[float, float]],
                pad: float = 0.12, min_keep: float = 0.15) -> list[list[float]]:
    """Silinəcək aralıqlardan saxlanılacaq aralıqları çıxarır (kənarlarda nəfəs payı ilə)."""
    keep: list[list[float]] = []
    t = start
    for a, b in sorted(remove):
        a2, b2 = a + pad, b - pad
        if b2 - a2 <= 0:
            continue
        if a2 - t >= min_keep:
            keep.append([round(t, 3), round(a2, 3)])
        t = max(t, b2)
    if end - t >= min_keep:
        keep.append([round(t, 3), round(end, 3)])
    return keep
