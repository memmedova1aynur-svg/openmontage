"""Layihə məlumatından FFmpeg ilə MP4 render (həmişə ORİJİNAL fayllardan).

Önizləmə ilə eyni layihə JSON-u istifadə olunur. Video kliplər kadr sərhədinə
yuvarlaqlaşdırılır, bağlı səs həmin başlanğıcı götürür — sürüşmə yığılmır.

Klip parametrləri (hamısı istəyə bağlı, yalnız istifadəçi seçəndə):
  frame  — kadraj (reframe.py), rotate — dərəcə
  adjust — {mirror, brightness, contrast, saturation, temperature}
Layihə parametrləri:
  aspect, mix {speech, music, sfx, voice, duck}, branding {logo, end}, mirrorAll
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
HDR_TRC = {"smpte2084", "arib-std-b67"}
DEFAULT_MIX = {"speech": 1.0, "music": 1.0, "sfx": 1.0, "voice": 1.0, "duck": False}
LOGO_POS = {
    "top-left": ("W*0.04", "H*0.03"), "top-right": ("W-w-W*0.04", "H*0.03"),
    "bottom-left": ("W*0.04", "H-h-H*0.03"), "bottom-right": ("W-w-W*0.04", "H-h-H*0.03"),
    "center": ("(W-w)/2", "(H-h)/2"),
}


def _font() -> str | None:
    for f in FONT_CANDIDATES:
        if Path(f).is_file():
            return f
    return None


def _even(x: float) -> int:
    return max(2, int(x) // 2 * 2)


def fps_of(project: dict[str, Any]) -> tuple[float, str]:
    rate = project.get("fpsRate")
    if isinstance(rate, str) and "/" in rate:
        n, d = rate.split("/")
        try:
            v = float(n) / float(d)
            if 1 <= v <= 120:
                return v, rate
        except (ValueError, ZeroDivisionError):
            pass
    f = float(project.get("fps") or 30)
    return f, str(int(f)) if f == int(f) else f"{f:.3f}"


def end_card(project: dict[str, Any]) -> dict[str, Any] | None:
    e = ((project.get("branding") or {}).get("end") or {})
    if not e.get("enabled"):
        return None
    return {**e, "duration": max(1.0, min(10.0, float(e.get("duration") or 3)))}


def render_plan(project: dict[str, Any]) -> dict[str, Any]:
    validate(project)
    fps, _ = fps_of(project)
    kinds = track_kinds(project)
    lay = layout(project)
    vplan, vstart, frames = [], {}, 0
    for c in video_clips(project):
        n = max(1, round(clip_dur(c) * fps))
        vstart[c["id"]] = frames / fps
        vplan.append({"clip": c, "start": frames / fps, "frames": n, "dur": n / fps})
        frames += n
    video_end = frames / fps
    aplan, tplan = [], []
    for c in project["clips"]:
        k = kinds[c["track"]]
        if k in AUDIO_KINDS:
            link = c.get("linkedTo")
            if link and link in vstart:
                start, dur = vstart[link], max(1, round(clip_dur(c) * fps)) / fps
            else:
                start, dur = lay[c["id"]][0], clip_dur(c)
            aplan.append({"clip": c, "kind": k, "start": start, "dur": dur})
        elif k == "text":
            s, e = lay[c["id"]]
            tplan.append({"clip": c, "start": s, "end": e})
    main = max([video_end] + [a["start"] + a["dur"] for a in aplan] + [t["end"] for t in tplan] + [0.0])
    ec = end_card(project)
    total = main + (ec["duration"] if ec else 0)
    return {"fps": fps, "video": vplan, "audio": aplan, "text": tplan, "videoEnd": video_end,
            "main": round(main, 3), "endCard": ec, "total": round(total, 3)}


def output_dims(project: dict[str, Any]) -> tuple[int, int]:
    return _even(project.get("width") or 1280), _even(project.get("height") or 720)


def _lerp_expr(keys: list[dict[str, float]], field: str, t0: float) -> str:
    """Açar kadrlar arasında xətti interpolyasiya (t — klipin daxili vaxtı)."""
    ks = sorted(keys, key=lambda k: k["t"])
    if len(ks) == 1:
        return f"{ks[0][field]:.5f}"
    expr = f"{ks[-1][field]:.5f}"
    for a, b in reversed(list(zip(ks, ks[1:]))):
        ta, tb = a["t"] - t0, b["t"] - t0
        span = max(1e-3, tb - ta)
        seg = f"({a[field]:.5f}+({b[field]:.5f}-{a[field]:.5f})*(t-{ta:.3f})/{span:.3f})"
        expr = f"if(lt(t,{tb:.3f}),{seg},{expr})"
    return f"if(lt(t,{ks[0]['t'] - t0:.3f}),{ks[0][field]:.5f},{expr})"


def video_chain(c: dict[str, Any], m: dict[str, Any], W: int, H: int, fps_str: str,
                mirror_all: bool, frames: int) -> str:
    """Bir video klip üçün filtr zənciri (input → [W x H], yuv420p)."""
    f: list[str] = []
    if m.get("hdr"):
        f.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
                 "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    fr = c.get("frame") or {}
    rot = float(fr.get("rotate") or 0)
    if abs(rot) > 0.05:
        # içəri doğru böyütmə: qara künc uydurulmur, kənar kəsilir
        f.append(f"rotate={rot}*PI/180:ow=iw:oh=ih:c=black")
        import math

        r = math.radians(abs(rot))
        sw, sh = float(m["width"]), float(m["height"])
        z = math.cos(r) + max(sw / sh, sh / sw) * math.sin(r)
        f.append(f"scale=iw*{z:.4f}:ih*{z:.4f},crop=iw/{z:.4f}:ih/{z:.4f}")
    if fr.get("mode") in ("auto", "manual") and fr.get("keys"):
        s = float(fr.get("s") or 1)
        bw, bh = float(fr.get("baseW") or 1), float(fr.get("baseH") or 1)
        cw = f"iw*{bw * s:.5f}"
        ch = f"ih*{bh * s:.5f}"
        cx = _lerp_expr(fr["keys"], "cx", float(c["srcIn"]))
        cy = _lerp_expr(fr["keys"], "cy", float(c["srcIn"]))
        f.append(f"crop=w='{cw}':h='{ch}':x='max(0,min(iw-ow,iw*({cx})-ow/2))':"
                 f"y='max(0,min(ih-oh,ih*({cy})-oh/2))'")
    adj = c.get("adjust") or {}
    if bool(adj.get("mirror")) ^ bool(mirror_all):
        f.append("hflip")
    b, ct, sat = float(adj.get("brightness") or 0), float(adj.get("contrast") or 1), float(adj.get("saturation") or 1)
    if abs(b) > 1e-3 or abs(ct - 1) > 1e-3 or abs(sat - 1) > 1e-3:
        f.append(f"eq=brightness={b:.3f}:contrast={ct:.3f}:saturation={sat:.3f}")
    temp = float(adj.get("temperature") or 6500)
    if abs(temp - 6500) > 50:
        f.append(f"colortemperature=temperature={temp:.0f}")
    f.append(f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos")
    f.append(f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps_str}")
    f.append(f"setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1,trim=end_frame={frames},"
             f"setpts=PTS-STARTPTS,format=yuv420p")
    return ",".join(f)


def build_command(project: dict[str, Any], media_root: Path, out: Path, workdir: Path,
                  logo_path: Path | None = None) -> list[str]:
    plan = render_plan(project)
    if plan["total"] <= 0:
        raise ValueError("Zaman xətti boşdur")
    fps, fps_str = fps_of(project)
    W, H = output_dims(project)
    media = media_map(project)
    mix = {**DEFAULT_MIX, **(project.get("mix") or {})}
    mirror_all = bool(project.get("mirrorAll"))
    args: list[str] = ["ffmpeg", "-y", "-v", "error", "-progress", "pipe:1", "-nostats"]
    filters: list[str] = []
    idx = 0

    def add_input(m: dict[str, Any], ss: float, t: float) -> int:
        nonlocal idx
        if m.get("isImage"):
            args.extend(["-loop", "1", "-framerate", fps_str, "-t", f"{t + 0.1:.4f}", "-i", str(media_root / m["file"])])
        else:
            args.extend(["-ss", f"{ss:.4f}", "-t", f"{t + 0.1:.4f}", "-i", str(media_root / m["file"])])
        idx += 1
        return idx - 1

    vlabels = []
    for i, v in enumerate(plan["video"]):
        c = v["clip"]
        m = media[c["media"]]
        k = add_input(m, float(c["srcIn"]), v["dur"])
        filters.append(f"[{k}:v]{video_chain(c, m, W, H, fps_str, mirror_all, v['frames'])}[v{i}]")
        vlabels.append(f"[v{i}]")
    main = plan["main"]
    if vlabels:
        filters.append(f"{''.join(vlabels)}concat=n={len(vlabels)}:v=1:a=0[vcat]")
        pad = main - plan["videoEnd"]
        filters.append(f"[vcat]tpad=stop_mode=add:stop_duration={pad:.4f}:color=black[vbase]" if pad > 1e-3
                       else "[vcat]null[vbase]")
    else:
        filters.append(f"color=c=black:s={W}x{H}:r={fps_str}:d={main:.4f},format=yuv420p[vbase]")

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
        color = (c.get("color") or "white").replace("#", "0x")
        box = (c.get("bg") or "black@0.55").replace("#", "0x")
        filters.append(
            f"[{cur}]drawtext=fontfile='{font}':textfile='{tf}':fontsize={size}:fontcolor={color}:"
            f"box=1:boxcolor={box}:boxborderw={max(6, size // 4)}:line_spacing={size // 5}:"
            f"x=(w-text_w)/2:y={y}:enable='between(t,{t['start']:.3f},{t['end']:.3f})'[vt{i}]")
        cur = f"vt{i}"

    logo = ((project.get("branding") or {}).get("logo") or {})
    if logo.get("enabled") and logo_path and logo_path.is_file():
        args.extend(["-loop", "1", "-t", f"{main:.4f}", "-i", str(logo_path)])
        li = idx
        idx += 1
        lw = max(16, int(W * float(logo.get("size") or 0.18)))
        x, y = LOGO_POS.get(logo.get("position") or "top-right", LOGO_POS["top-right"])
        op = float(logo.get("opacity") or 1)
        filters.append(f"[{li}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={op:.2f}[lg]")
        filters.append(f"[{cur}][lg]overlay=x={x}:y={y}:shortest=1[vlogo]")
        cur = "vlogo"

    ec = plan["endCard"]
    if ec:
        d = ec["duration"]
        bg = (ec.get("bg") or "#000000").replace("#", "0x")
        filters.append(f"color=c={bg}:s={W}x{H}:r={fps_str}:d={d:.4f},format=yuv420p[ecb]")
        ecur = "ecb"
        if ec.get("showLogo") and logo_path and logo_path.is_file():
            args.extend(["-loop", "1", "-t", f"{d:.4f}", "-i", str(logo_path)])
            li = idx
            idx += 1
            filters.append(f"[{li}:v]scale={int(W * 0.45)}:-1,format=rgba,fade=t=in:st=0:d=0.6:alpha=1[ecl]")
            filters.append(f"[{ecur}][ecl]overlay=x=(W-w)/2:y=H*0.30-h/2:shortest=1[ec1]")
            ecur = "ec1"
        lines = [(ec.get("cta") or "").strip(), (ec.get("contact") or "").strip()]
        for j, (txt, ypos, scale) in enumerate(zip(lines, ("h*0.58", "h*0.70"), (0.055, 0.035))):
            if not txt or not font:
                continue
            tf = workdir / f"end_{j}.txt"
            tf.write_text(txt, encoding="utf-8")
            col = (ec.get("color") or "#FFFFFF").replace("#", "0x")
            filters.append(f"[{ecur}]drawtext=fontfile='{font}':textfile='{tf}':fontsize={int(H * scale)}:"
                           f"fontcolor={col}:x=(w-text_w)/2:y={ypos}:alpha='min(1,max(0,(t-{0.3 + 0.3 * j:.1f})/0.5))'[ec{j + 2}]")
            ecur = f"ec{j + 2}"
        filters.append(f"[{ecur}]fade=t=in:st=0:d=0.4[ecf]")
        filters.append(f"[{cur}][ecf]concat=n=2:v=1:a=0[vfinal]")
        cur = "vfinal"
    filters.append(f"[{cur}]null[vout]")

    total = plan["total"]
    buses: dict[str, list[str]] = {}
    for i, a in enumerate(plan["audio"]):
        c = a["clip"]
        k = add_input(media[c["media"]], float(c["srcIn"]), a["dur"])
        ms = int(round(a["start"] * 1000))
        bus = "voice" if c.get("role") == "voiceover" else a["kind"]
        vol = float(c.get("volume", 1) if c.get("volume") is not None else 1) * float(mix.get(bus, 1))
        filters.append(f"[{k}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                       f"asetpts=PTS-STARTPTS,atrim=0:{a['dur']:.4f},volume={vol:.3f},adelay=delays={ms}:all=1[a{i}]")
        buses.setdefault(bus, []).append(f"[a{i}]")
    bus_out = []
    for bus, labs in buses.items():
        if len(labs) == 1:
            filters.append(f"{labs[0]}apad,atrim=0:{total:.4f}[bus_{bus}]")
        else:
            filters.append(f"{''.join(labs)}amix=inputs={len(labs)}:normalize=0:duration=longest,apad,atrim=0:{total:.4f}[bus_{bus}]")
        bus_out.append(bus)
    if mix.get("duck") and "music" in buses and ("speech" in buses or "voice" in buses):
        key = "speech" if "speech" in buses else "voice"
        filters.append(f"[bus_{key}]asplit=2[bk_main][bk_side]")
        filters.append("[bus_music][bk_side]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500:makeup=1[bus_music_d]")
        labels = [("bk_main" if b == key else "bus_music_d" if b == "music" else f"bus_{b}") for b in bus_out]
    else:
        labels = [f"bus_{b}" for b in bus_out]
    if labels:
        filters.append(f"{''.join(f'[{l}]' for l in labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,"
                       f"atrim=0:{total:.4f}[aout]" if len(labels) > 1 else f"[{labels[0]}]anull[aout]")
    else:
        filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total:.4f}[aout]")

    fg = workdir / "filter.txt"
    fg.write_text(";\n".join(filters), encoding="utf-8")
    args += [
        "-filter_complex_script", str(fg), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", project.get("exportPreset") or "medium", "-crf", str(project.get("exportCrf") or 18),
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        "-r", fps_str, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{total:.4f}", "-movflags", "+faststart", str(out),
    ]
    return args


def conversions(project: dict[str, Any]) -> list[str]:
    """İxracda hansı çevrilmələrin olacağını açıq izah edir."""
    out = []
    W, H = output_dims(project)
    fps, fps_str = fps_of(project)
    used = {c["media"] for c in project["clips"] if c.get("media")}
    for m in project["media"]:
        if m["id"] not in used:
            continue
        n = m["name"]
        if m.get("isImage"):
            out.append(f"{n}: şəkil → {W}×{H} hərəkətsiz video kadrları.")
            continue
        if not m.get("hasVideo"):
            continue
        if m.get("videoCodec") and m["videoCodec"] != "h264":
            out.append(f"{n}: {m['videoCodec'].upper()} → H.264 (telefon və sosial şəbəkə uyğunluğu üçün).")
        if m.get("hdr"):
            out.append(f"{n}: HDR ({m.get('colorTransfer')}) → SDR BT.709 tonemap (Instagram/TikTok-da rəng pozulmasın).")
        if (m.get("bitDepth") or 8) > 8:
            out.append(f"{n}: {m['bitDepth']}-bit → 8-bit.")
        if m.get("fps") and abs(float(m["fps"]) - fps) > 0.05:
            out.append(f"{n}: {m['fps']} fps → {fps_str} fps (layihə tezliyi).")
        clips = [c for c in project["clips"] if c.get("media") == m["id"] and (c.get("frame") or {}).get("mode") in ("auto", "manual")]
        if clips:
            fr = clips[0]["frame"]
            ch = float(m["height"]) * float(fr.get("baseH") or 1) * float(fr.get("s") or 1)
            ratio = H / max(1, ch)
            out.append(f"{n}: {fr.get('aspect')} kəsim; kəsilmiş hissə {int(ch)} px → {H} px "
                       f"({'böyütmə ' + format(ratio, '.2f') + 'x — bir az yumşalma ola bilər' if ratio > 1.05 else 'böyütmə yoxdur'}).")
        elif m.get("width") and (int(m["width"]) != W or int(m["height"]) != H):
            out.append(f"{n}: {m['width']}×{m['height']} → {W}×{H} (qara zolaqlarla sığdırılır, kəsilmir).")
    out.append("Effektlərlə montaj yenidən kodlaşdırma tələb edir: H.264 CRF 18 (yüksək keyfiyyət), AAC 192 kbit/s. "
               "Hər ixrac orijinal fayllardan yenidən hazırlanır, əvvəlki MP4 təkrar sıxılmır.")
    return out


def render(project: dict[str, Any], media_root: Path, out: Path,
           on_progress: Callable[[float], None] | None = None, logo_path: Path | None = None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out.with_suffix(".part.mp4")
    workdir = Path(tempfile.mkdtemp(prefix="montaj_render_"))
    try:
        cmd = build_command(project, media_root, tmp_out, workdir, logo_path)
        total = render_plan(project)["total"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.stdout is not None
        for line in proc.stdout:
            if line.startswith("out_time_us=") and on_progress and total > 0:
                try:
                    on_progress(min(0.99, int(line.split("=", 1)[1]) / 1e6 / total))
                except ValueError:
                    pass
        err = proc.stderr.read() if proc.stderr else ""
        if proc.wait() != 0:
            raise RuntimeError(f"FFmpeg render xətası: {err.strip()[-1200:]}")
        tmp_out.replace(out)
        if on_progress:
            on_progress(1.0)
        return out
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        if tmp_out.exists():
            tmp_out.unlink()
