"""Layihə məlumatından FFmpeg ilə MP4 render.

Önizləmə ilə eyni layihə JSON-u istifadə olunur. Video kliplər kadr sərhədinə
yuvarlaqlaşdırılır, bağlı səs isə həmin kvantlaşdırılmış başlanğıcı götürür —
beləliklə çoxlu kəsimdən sonra da səs-görüntü sürüşməsi yığılmır.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from montaj.model import AUDIO_KINDS, clip_dur, layout, media_map, track_kinds, validate, video_clips

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _font() -> str | None:
    for f in FONT_CANDIDATES:
        if Path(f).is_file():
            return f
    return None


def _even(x: int) -> int:
    return max(2, int(x) // 2 * 2)


def render_plan(project: dict[str, Any]) -> dict[str, Any]:
    """Kadr-kvantlaşdırılmış render planı (testlər üçün də istifadə olunur)."""
    validate(project)
    fps = int(project.get("fps") or 30)
    kinds = track_kinds(project)
    lay = layout(project)
    vplan: list[dict[str, Any]] = []
    vstart: dict[str, float] = {}
    frames = 0
    for c in video_clips(project):
        n = max(1, round(clip_dur(c) * fps))
        vstart[c["id"]] = frames / fps
        vplan.append({"clip": c, "start": frames / fps, "frames": n, "dur": n / fps})
        frames += n
    video_end = frames / fps
    aplan: list[dict[str, Any]] = []
    tplan: list[dict[str, Any]] = []
    for c in project["clips"]:
        k = kinds[c["track"]]
        if k in AUDIO_KINDS:
            link = c.get("linkedTo")
            if link and link in vstart:
                start = vstart[link]
                n = max(1, round(clip_dur(c) * fps))
                dur = n / fps
            else:
                start = lay[c["id"]][0]
                dur = clip_dur(c)
            aplan.append({"clip": c, "start": start, "dur": dur})
        elif k == "text":
            s, e = lay[c["id"]]
            tplan.append({"clip": c, "start": s, "end": e})
    total = max([video_end] + [a["start"] + a["dur"] for a in aplan] + [t["end"] for t in tplan] + [0.0])
    return {"fps": fps, "video": vplan, "audio": aplan, "text": tplan,
            "videoEnd": video_end, "total": round(total, 3)}


def build_command(project: dict[str, Any], media_root: Path, out: Path, workdir: Path) -> list[str]:
    plan = render_plan(project)
    if plan["total"] <= 0:
        raise ValueError("Zaman xətti boşdur")
    fps = plan["fps"]
    W, H = _even(project.get("width") or 1280), _even(project.get("height") or 720)
    media = media_map(project)
    args: list[str] = ["ffmpeg", "-y", "-v", "error", "-progress", "pipe:1", "-nostats"]
    filters: list[str] = []
    idx = 0

    def add_input(m: dict[str, Any], ss: float, t: float) -> int:
        nonlocal idx
        args.extend(["-ss", f"{ss:.4f}", "-t", f"{t + 0.1:.4f}", "-i", str(media_root / m["file"])])
        idx += 1
        return idx - 1

    vlabels: list[str] = []
    for i, v in enumerate(plan["video"]):
        c = v["clip"]
        k = add_input(media[c["media"]], float(c["srcIn"]), v["dur"])
        lab = f"v{i}"
        filters.append(
            f"[{k}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps},"
            f"setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1,"
            f"trim=end_frame={v['frames']},setpts=PTS-STARTPTS,format=yuv420p[{lab}]"
        )
        vlabels.append(f"[{lab}]")
    total = plan["total"]
    if vlabels:
        filters.append(f"{''.join(vlabels)}concat=n={len(vlabels)}:v=1:a=0[vcat]")
        pad = total - plan["videoEnd"]
        if pad > 1e-3:
            filters.append(f"[vcat]tpad=stop_mode=add:stop_duration={pad:.4f}:color=black[vbase]")
        else:
            filters.append("[vcat]null[vbase]")
    else:
        filters.append(f"color=c=black:s={W}x{H}:r={fps}:d={total:.4f},format=yuv420p[vbase]")

    font = _font()
    cur = "vbase"
    for i, t in enumerate(plan["text"]):
        c = t["clip"]
        text = (c.get("text") or "").strip()
        if not text or not font:
            continue
        tf = workdir / f"text_{i}.txt"
        tf.write_text(text, encoding="utf-8")
        size = max(12, int(H * float(c.get("size") or 0.06)))
        pos = c.get("position") or "bottom"
        y = {"top": "h*0.08", "center": "(h-text_h)/2"}.get(pos, "h*0.88-text_h")
        nxt = f"vt{i}"
        filters.append(
            f"[{cur}]drawtext=fontfile='{font}':textfile='{tf}':fontsize={size}:"
            f"fontcolor=white:box=1:boxcolor=black@0.55:boxborderw={max(6, size // 4)}:"
            f"line_spacing={size // 5}:x=(w-text_w)/2:y={y}:"
            f"enable='between(t,{t['start']:.3f},{t['end']:.3f})'[{nxt}]"
        )
        cur = nxt
    filters.append(f"[{cur}]null[vout]")

    alabels: list[str] = []
    for i, a in enumerate(plan["audio"]):
        c = a["clip"]
        k = add_input(media[c["media"]], float(c["srcIn"]), a["dur"])
        ms = int(round(a["start"] * 1000))
        vol = float(c.get("volume", 1) if c.get("volume") is not None else 1)
        lab = f"a{i}"
        filters.append(
            f"[{k}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"asetpts=PTS-STARTPTS,atrim=0:{a['dur']:.4f},volume={vol:.3f},"
            f"adelay=delays={ms}:all=1[{lab}]"
        )
        alabels.append(f"[{lab}]")
    if alabels:
        filters.append(
            f"{''.join(alabels)}amix=inputs={len(alabels)}:normalize=0:duration=longest,"
            f"apad,atrim=0:{total:.4f}[aout]"
        )
    else:
        filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total:.4f}[aout]")

    fg = workdir / "filter.txt"
    fg.write_text(";\n".join(filters), encoding="utf-8")
    args += [
        "-filter_complex_script", str(fg),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{total:.4f}", "-movflags", "+faststart", str(out),
    ]
    return args


def render(project: dict[str, Any], media_root: Path, out: Path,
           on_progress: Callable[[float], None] | None = None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out.with_suffix(".part.mp4")
    workdir = Path(tempfile.mkdtemp(prefix="montaj_render_"))
    try:
        cmd = build_command(project, media_root, tmp_out, workdir)
        total = render_plan(project)["total"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.stdout is not None
        for line in proc.stdout:
            if line.startswith("out_time_us=") and on_progress and total > 0:
                try:
                    us = int(line.split("=", 1)[1])
                    on_progress(min(0.99, us / 1e6 / total))
                except ValueError:
                    pass
        err = proc.stderr.read() if proc.stderr else ""
        if proc.wait() != 0:
            raise RuntimeError(f"FFmpeg render xətası: {err.strip()[-800:]}")
        tmp_out.replace(out)
        if on_progress:
            on_progress(1.0)
        return out
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        if tmp_out.exists():
            tmp_out.unlink()
