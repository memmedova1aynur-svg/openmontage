"""Layihə məlumatından FFmpeg ilə MP4 render (həmişə ORİJİNAL fayllardan).

Önizləmə ilə eyni layihə JSON-u istifadə olunur. Video kliplər kadr sərhədinə
yuvarlaqlaşdırılır, bağlı səs həmin başlanğıcı götürür — sürüşmə yığılmır.

Klip parametrləri (hamısı istəyə bağlı, yalnız istifadəçi seçəndə):
  frame  — kadraj (reframe.py), rotate — dərəcə
  adjust — {mirror, brightness, contrast, saturation, vibrance, depth, temperature, soften, sharpen, denoise, shadows}
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
    aplan, tplan, oplan = [], [], []
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
            if c.get("hidden"):
                continue
            s, e = lay[c["id"]]
            tplan.append({"clip": c, "start": s, "end": e})
        elif k == "overlay":
            s, e = lay[c["id"]]
            oplan.append({"clip": c, "start": s, "dur": e - s, "frames": max(1, round((e - s) * fps))})
    main = max([video_end] + [a["start"] + a["dur"] for a in aplan] + [t["end"] for t in tplan] + [0.0])
    ec = end_card(project)
    total = main + (ec["duration"] if ec else 0)
    return {"fps": fps, "video": vplan, "overlay": oplan, "audio": aplan, "text": tplan, "videoEnd": video_end,
            "main": round(main, 3), "endCard": ec, "total": round(total, 3)}


def _afades(c: dict[str, Any], dur: float) -> str:
    """Yumşaq səs giriş-çıxışı (klipin fadeIn/fadeOut saniyələri)."""
    out = ""
    fi = float(c.get("fadeIn") or 0)
    fo = float(c.get("fadeOut") or 0)
    if fi > 0:
        out += f",afade=t=in:st=0:d={min(fi, dur):.3f}"
    if fo > 0:
        out += f",afade=t=out:st={max(0.0, dur - fo):.3f}:d={min(fo, dur):.3f}"
    return out


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


HDR_TO_SDR = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
              "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def color_filters(adj: dict[str, Any]) -> list[str]:
    """Rəng düzəlişi (ölçüdən əvvəl). Render və `session looks` eyni funksiyanı işlədir."""
    f: list[str] = []
    dn = float(adj.get("denoise") or 0)
    if dn > 0.01:  # ştativ çəkilişi: güclü zaman (kadrlar arası), yüngül məkan təmizləməsi — detal qorunur
        f.append(f"hqdn3d=luma_spatial={2.2 * dn:.2f}:chroma_spatial={3.5 * dn:.2f}:luma_tmp={13 * dn:.2f}:chroma_tmp={15 * dn:.2f}")
    sh = float(adj.get("shadows") or 0)
    if sh > 0.01:  # qaranlıq hissələri yumşaq açır, işıqlı yerlər yanmır
        f.append(f"curves=master='0/0 0.12/{0.12 + 0.07 * sh:.4f} 0.35/{0.35 + 0.08 * sh:.4f} 0.7/{0.7 + 0.03 * sh:.4f} 1/1'")
    b, ct, sat = float(adj.get("brightness") or 0), float(adj.get("contrast") or 1), float(adj.get("saturation") or 1)
    gm = float(adj.get("gamma") or 1)
    if abs(b) > 1e-3 or abs(ct - 1) > 1e-3 or abs(sat - 1) > 1e-3 or abs(gm - 1) > 1e-3:
        f.append(f"eq=brightness={b:.3f}:contrast={ct:.3f}:saturation={sat:.3f}" + (f":gamma={gm:.3f}" if abs(gm - 1) > 1e-3 else ""))
    depth = float(adj.get("depth") or 0)
    if depth > 0.01:  # qaranlıq və işıqlı hissələrə yüngül dərinlik (S-əyri)
        lo, hi = 0.05 - 0.015 * min(depth, 2), 0.95 + 0.015 * min(depth, 2)
        f.append(f"curves=master='0/0 0.05/{lo:.4f} 0.95/{hi:.4f} 1/1'")
    vib = float(adj.get("vibrance") or 0)
    if vib > 0.005:  # solğun rəngləri canlandırır, onsuz da doymuş rənglərə (dəriyə) az təsir edir
        f.append(f"vibrance=intensity={min(vib, 1):.3f}")
    soft = float(adj.get("soften") or 0)
    if soft > 0.01:
        # yüngül yumşaltma: kənarları qoruyur, bütün kadra tətbiq olunur (üz seçilmir)
        f.append(f"smartblur=lr=2.0:ls={min(1.0, 0.2 + 0.6 * soft):.2f}:lt=8")
    temp = float(adj.get("temperature") or 6500)
    if abs(temp - 6500) > 50:
        f.append(f"colortemperature=temperature={temp:.0f}")
    return f


def sharpen_filter(adj: dict[str, Any]) -> list[str]:
    """Yüngül kəskinlik (yalnız parlaqlıq), çıxış ölçüsündə tətbiq olunur."""
    sharp = float(adj.get("sharpen") or 0)
    return [f"unsharp=5:5:{min(1.0, sharp):.2f}:5:5:0"] if sharp > 0.01 else []


def video_chain(c: dict[str, Any], m: dict[str, Any], W: int, H: int, fps_str: str,
                mirror_all: bool, frames: int) -> str:
    """Bir video klip üçün filtr zənciri (input → [W x H], yuv420p)."""
    f: list[str] = []
    if m.get("hdr"):
        f.append(HDR_TO_SDR)
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
    f += color_filters(adj)
    f.append(f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos")
    f += sharpen_filter(adj)
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
    # B-roll / PIP: əsas videonun üstündə, yazı və altyazının altında; səsi əsas danışığı əvəz etmir.
    # cover_pip: səhnə bütün kadrı tutur, danışan isə küncdə dairədə qalır (motion graphics videoları)
    cpips = [o for o in plan["overlay"] if o["clip"].get("mode") == "cover_pip"]
    spk_labels: list[str] = []
    if cpips:
        from PIL import Image, ImageDraw

        D = _even(W * float(cpips[0]["clip"].get("pip", {}).get("size", 0.3)))
        mask = Image.new("L", (D, D), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, D - 1, D - 1), fill=255)
        mask.save(workdir / "pip_mask.png")
        ring = Image.new("RGBA", (D + 12, D + 12), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((2, 2, D + 9, D + 9), outline=(255, 255, 255, 235), width=6)
        ring.save(workdir / "pip_ring.png")
        n = len(cpips)
        filters.append(f"[{cur}]split=2[vb_main][vb_spk]")
        filters.append(f"[vb_spk]split={n}" + "".join(f"[spk{i}]" for i in range(n)) if n > 1 else "[vb_spk]null[spk0]")
        cur = "vb_main"
        args.extend(["-loop", "1", "-i", str(workdir / "pip_mask.png")])
        mi = idx
        idx += 1
        filters.append(f"[{mi}:v]format=gray,split={n}" + "".join(f"[pm{i}]" for i in range(n)) if n > 1 else f"[{mi}:v]format=gray[pm0]")
        args.extend(["-loop", "1", "-i", str(workdir / "pip_ring.png")])
        ri = idx
        idx += 1
        filters.append(f"[{ri}:v]format=rgba,split={n}" + "".join(f"[pr{i}]" for i in range(n)) if n > 1 else f"[{ri}:v]format=rgba[pr0]")
        spk_labels = [f"spk{i}" for i in range(n)]
    cp_i = 0
    for i, o in enumerate(plan["overlay"]):
        c = o["clip"]
        m = media[c["media"]]
        k = add_input(m, float(c["srcIn"]), o["dur"])
        pip = c.get("pip") if c.get("mode") == "pip" else None
        if c.get("mode") == "sticker":  # şəffaf obraz (ProRes 4444 alfa) — tam kadr ölçüsündə, alfa qorunur
            chain = (f"scale={W}:{H}:flags=lanczos,fps={fps_str},setpts=PTS-STARTPTS,"
                     f"tpad=stop_mode=clone:stop_duration=1,trim=end_frame={o['frames']},setpts=PTS-STARTPTS,format=yuva420p")
            x = y = "0"
        elif pip:  # PIP mənbənin öz nisbətində (qara zolaqsız), nazik ağ çərçivə ilə
            sc = min(0.9, max(0.15, float(pip.get("scale", 0.42))))
            bw = max(2, int(W * 0.006))
            adj = c.get("adjust") or {}
            parts = ([HDR_TO_SDR] if m.get("hdr") else []) + color_filters(adj) + [
                f"scale={_even(W * sc) - 2 * bw}:-2:flags=lanczos"] + sharpen_filter(adj) + [
                f"pad=iw+{2 * bw}:ih+{2 * bw}:{bw}:{bw}:color=white", f"fps={fps_str}", "setpts=PTS-STARTPTS",
                f"tpad=stop_mode=clone:stop_duration=1,trim=end_frame={o['frames']}", "setpts=PTS-STARTPTS", "format=yuv420p"]
            chain = ",".join(parts)
            x = f"'max(0,min(W-w,W*{float(pip.get('x', 0.5)):.4f}-w/2))'"
            y = f"'max(0,min(H-h,H*{float(pip.get('y', 0.13)):.4f}-h/2))'"
        else:
            chain = video_chain(c, m, W, H, fps_str, False, o["frames"])
            x = y = "0"
        filters.append(f"[{k}:v]{chain},setpts=PTS+{o['start']:.4f}/TB[ov{i}]")
        a_t, b_t = o["start"], o["start"] + o["dur"] - 0.5 / fps
        filters.append(f"[{cur}][ov{i}]overlay=x={x}:y={y}:eof_action=pass:enable='between(t,{a_t:.4f},{b_t:.4f})'[vo{i}]")
        cur = f"vo{i}"
        if c.get("mode") == "cover_pip":  # danışan: kadrın üz hissəsi dairədə, sol-aşağıda (sağda Reels düymələri var)
            pp = c.get("pip") or {}
            D = _even(W * float(pp.get("size", 0.3)))
            px = int(W * float(pp.get("x", 0.07)))
            py = int(H * float(pp.get("y", 0.6)) - D / 2)
            j = cp_i
            cp_i += 1
            filters.append(f"[{spk_labels[j]}]crop=iw*0.62:iw*0.62:iw*0.19:max(0\\,ih*0.36-iw*0.31),scale={D}:{D},format=rgba[sq{j}];"
                           f"[sq{j}][pm{j}]alphamerge[pc{j}]")
            filters.append(f"[{cur}][pc{j}]overlay=x={px}:y={py}:enable='between(t,{a_t:.4f},{b_t:.4f})'[vp{j}];"
                           f"[vp{j}][pr{j}]overlay=x={px - 6}:y={py - 6}:enable='between(t,{a_t:.4f},{b_t:.4f})'[vr{j}]")
            cur = f"vr{j}"
    from montaj import graphics as G

    gfx = [t for t in plan["text"] if G.is_graphic(t["clip"])]
    for i, t in enumerate(plan["text"]):
        c = t["clip"]
        if G.is_graphic(c):
            continue
        text = (c.get("text") or "").strip()
        from montaj import fonts as _fonts
        cfont = _fonts.ttf_path(c.get("font"), c.get("weight")) if c.get("font") else font
        if not text or not cfont:
            continue
        tf = workdir / f"text_{i}.txt"
        tf.write_text(text, encoding="utf-8")
        size = max(12, int(H * float(c.get("size") or 0.06)))
        pos = c.get("position") or "bottom"
        y = {"top": "h*0.08", "center": "(h-text_h)/2"}.get(pos, "h*0.88-text_h")
        xexpr = "(w-text_w)/2"
        if c.get("x") is not None and c.get("y") is not None:
            # telefonda sürüşdürülmüş yer: mərkəz nöqtəsi (0..1), kadrdan çıxmasın
            xexpr = f"max(0\\,min(w-text_w\\,w*{float(c['x']):.4f}-text_w/2))"
            y = f"max(0\\,min(h-text_h\\,h*{float(c['y']):.4f}-text_h/2))"
        color = (c.get("color") or "white").replace("#", "0x")
        bg = c.get("bg") or "black@0.55"
        boxopt = ("box=0:shadowcolor=black@0.7:shadowx=2:shadowy=2" if bg == "none"
                  else f"box=1:boxcolor={bg.replace('#', '0x')}:boxborderw={max(6, size // 4)}")
        filters.append(
            f"[{cur}]drawtext=fontfile='{cfont}':textfile='{tf}':fontsize={size}:fontcolor={color}:"
            f"{boxopt}:line_spacing={size // 5}:"
            f"x={xexpr}:y={y}:enable='between(t,{t['start']:.3f},{t['end']:.3f})'[vt{i}]")
        cur = f"vt{i}"

    if gfx:
        theme = (project.get("brand") or {}).get("theme") or {}
        items, caps, others = [], [], []
        for t in gfx:
            c = dict(t["clip"], _start=t["start"])
            for k, ptime in enumerate(G.state_points(c)):
                items.append((f"{c['id']}__{k}", c, ptime))
            (caps if c["type"] == "caption" else others).append(c)
        rast = G.rasterize(items, W, H, theme, workdir)
        for c in others:  # kartlar, başlıqlar, vurğular — animasiya ilə
            pts = G.state_points(c)
            dur = float(c["srcOut"]) - float(c["srcIn"])
            for k, ptime in enumerate(pts):
                a = c["_start"] + ptime
                b = c["_start"] + (pts[k + 1] if k + 1 < len(pts) else dur)
                info = rast[f"{c['id']}__{k}"]
                args.extend(["-loop", "1", "-framerate", fps_str, "-t", f"{b - a + 0.1:.4f}", "-i", info["file"]])
                nxt = f"vg{idx}"
                filters.append(G.overlay_chain(c, k, len(pts), a, b, W, H, fps_str, idx, cur, nxt))
                idx += 1
                cur = nxt
        track = G.caption_track(caps, W, H, fps, main, rast, workdir)
        if track:
            args.extend(["-i", str(track)])
            filters.append(f"[{idx}:v]format=rgba[capt];[{cur}][capt]overlay=0:0:eof_action=pass[vcap]")
            idx += 1
            cur = "vcap"

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
    clean = project.get("voiceClean") or {}
    for i, a in enumerate(plan["audio"]):
        c = a["clip"]
        m = media[c["media"]]
        vc = clean.get(m["id"]) if a["kind"] == "speech" else None
        if vc and vc.get("file") and (media_root / vc["file"]).is_file():
            m = {**m, "file": vc["file"], "isImage": False}  # arxa səsi təmizlənmiş danışıq (orijinal dəyişmir)
        k = add_input(m, float(c["srcIn"]), a["dur"])
        ms = int(round(a["start"] * 1000))
        bus = "voice" if c.get("role") == "voiceover" else a["kind"]
        vol = float(c.get("volume", 1) if c.get("volume") is not None else 1) * float(mix.get(bus, 1))
        filters.append(f"[{k}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                       f"asetpts=PTS-STARTPTS,atrim=0:{a['dur']:.4f},volume={vol:.3f}{_afades(c, a['dur'])},adelay=delays={ms}:all=1[a{i}]")
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


LOUDNESS_TARGET = -14.0   # LUFS (Instagram/Reels üçün geniş yayılmış hədəf); layihədə "loudnessTarget": null — söndürür
TRUE_PEAK = -1.5


def measure_loudness(path: Path, target: float = LOUDNESS_TARGET) -> dict[str, float] | None:
    """EBU R128 ölçmə (loudnorm birinci keçid). Səs yoxdursa None."""
    import json as _json

    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
                        f"loudnorm=I={target}:TP={TRUE_PEAK}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    i, j = txt.rfind("{"), txt.rfind("}")
    if r.returncode != 0 or i < 0 or j < i:
        return None
    try:
        d = _json.loads(txt[i:j + 1])
        return {k: float(d[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}
    except (KeyError, ValueError):
        return None


def normalize_loudness(src: Path, dst: Path, target: float = LOUDNESS_TARGET) -> dict[str, Any]:
    """Səsi hədəf səviyyəyə gətirir (xətti düzəliş, ikinci keçid). Video axını KOPYALANIR — təkrar kodlama yoxdur."""
    m = measure_loudness(src, target)
    if not m or m["input_i"] < -70:  # səssiz və ya ölçülmədi
        shutil.copyfile(src, dst)
        return {"applied": False}
    af = (f"loudnorm=I={target}:TP={TRUE_PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          # yumşaq limiter: AAC-dən sonra da pik −1.5 dBTP-dən aşağı qalsın (telefonda təhrif olmasın)
          f"aresample=192000,alimiter=limit=0.78:attack=3:release=60:level=false,aresample=48000")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
                    "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(dst)], check=True)
    return {"applied": True, "before": round(m["input_i"], 1), "target": target}


DELIVERY_CAP_MB = 40.0   # telefondan söhbətdən rahat endirilən ölçü


def delivery_copy(src: Path, dst: Path, cap_mb: float = DELIVERY_CAP_MB) -> Path | None:
    """Fayl həddən böyükdürsə, eyni ölçü/kadr tezliyində yüngül H.264 nüsxə (səs kopyalanır). Kiçikdirsə None."""
    size_mb = src.stat().st_size / 1e6
    if size_mb <= cap_mb:
        return None
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                               capture_output=True, text=True, check=True).stdout.strip())
    kbps = int(cap_mb * 0.94 * 8000 / max(dur, 1) - 200)  # 6% ehtiyat, səs ~192k
    kbps = max(1500, min(kbps, 16000))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264",
                    "-preset", "medium", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.25)}k", "-bufsize", f"{kbps * 2}k",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(dst)], check=True)
    return dst


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
        target = project.get("loudnessTarget", LOUDNESS_TARGET)
        if target is not None:
            norm = tmp_out.with_suffix(".norm.mp4")
            normalize_loudness(tmp_out, norm, float(target))
            norm.replace(tmp_out)
        tmp_out.replace(out)
        if on_progress:
            on_progress(1.0)
        return out
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        if tmp_out.exists():
            tmp_out.unlink()
