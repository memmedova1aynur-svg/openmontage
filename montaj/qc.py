"""Keyfiyyət nəzarəti (videoqrafiya: "ixrac edilmiş fayl da ayrıca yoxlanmalıdır", "materialı tanımaq").

* intake — material gələndə: fps (qarışıq/dəyişkən), ölçü və keyfiyyət ehtiyatı, HDR, səsin partlaması (clipping) və zəifliyi,
  kliplər arası ağ balansı/işıq fərqi, kəskinlik, titrəmə. Montajdan ƏVVƏL xəbər verir (sonradan sürpriz olmasın).
* final — yekun MP4: qara kadr, donmuş kadr, səs pikləri və qəfil sıçrayış, yazıların oxunma müddəti, texniki uyğunluq.
Hamısı ölçmədir; qulaqla dinləmə və gözlə baxma əvəz olunmur — yoxlanmayanı yoxlanmış kimi təqdim etmə.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

READ_WPS = 3.0     # oxunma sürəti: saniyədə ~3 söz (qısa ekran mətni üçün ehtiyatlı)
READ_MIN = 1.2     # ən qısa ekran vaxtı, s


# ---------------------------------------------------------------------------
# Qəbul yoxlaması
# ---------------------------------------------------------------------------

def _fps(s: str | None) -> float:
    try:
        a, b = (s or "0/1").split("/")
        return float(a) / float(b or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _probe(src: Path) -> dict[str, Any]:
    js = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                    "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,pix_fmt,color_transfer,sample_rate,channels",
                                    "-of", "json", str(src)], capture_output=True, text=True, check=True).stdout)
    v = next((s for s in js.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in js.get("streams", []) if s.get("codec_type") == "audio"), {})
    return {"v": v, "a": a}


def _audio_stats(src: Path) -> dict[str, float] | None:
    from montaj import media as mediautil

    try:
        x = mediautil.read_mono(src, 16000)
    except subprocess.CalledProcessError:
        return None
    if not len(x):
        return None
    peak = float(np.abs(x).max())
    clipped = int((np.abs(x) > 0.995).sum())
    frames = x[: len(x) // 1600 * 1600].reshape(-1, 1600)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    speech = rms[rms > np.percentile(rms, 60)] if len(rms) > 10 else rms
    return {"peakDb": round(20 * np.log10(peak + 1e-9), 1), "clipped": clipped,
            "speechDb": round(float(20 * np.log10(np.median(speech) + 1e-9)), 1)}


def _frames_stats(src: Path, dur: float, n: int = 5) -> dict[str, float] | None:
    from montaj import event

    vals = []
    for k in range(n):
        t = dur * (k + 0.5) / n
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "2", "-vf", "scale=320:-2",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if not raw:
            continue
        a = np.frombuffer(raw, np.uint8)
        h = len(a) // 2 // (320 * 3)
        if h < 8:
            continue
        fr = a[: 2 * h * 320 * 3].reshape(2, h, 320, 3).astype(float)
        g0, g1 = fr[0].mean(axis=2), fr[1].mean(axis=2)
        vals.append((fr[0].mean(axis=(0, 1)), event._sharp(g0), float(np.abs(g1 - g0).mean())))
    if not vals:
        return None
    rgb = np.mean([v[0] for v in vals], axis=0)
    return {"bright": round(float(rgb.mean()), 1), "warm": round(float(rgb[0] - rgb[2]), 1),
            "sharp": round(float(np.median([v[1] for v in vals])), 3), "motion": round(float(np.median([v[2] for v in vals])), 2)}


def intake(project: dict[str, Any], root: Path, out_w: int | None = None) -> dict[str, Any]:
    """Material yoxlaması: hər fayl üçün ölçülər + xəbərdarlıqlar (az dilində), ümumi qeydlər."""
    items, notes = [], []
    vids = [m for m in project["media"] if m.get("hasVideo") and not m.get("isImage")
            and (m.get("source") or {}).get("type") not in ("generated", "music", "sfx")]
    out_w = out_w or int(project.get("width") or 1080)
    for m in vids:
        src = root / m["file"]
        pr = _probe(src)
        v = pr["v"]
        r, avg = _fps(v.get("r_frame_rate")), _fps(v.get("avg_frame_rate"))
        w = int(m.get("width") or v.get("width") or 0)
        h = int(m.get("height") or v.get("height") or 0)
        warn = []
        if r and avg and abs(r - avg) / r > 0.02:
            warn.append(f"dəyişkən kadr tezliyi (VFR: {avg:.2f} / {r:.2f} fps) — sabit fps-ə çevrilir, sinxron yoxlanmalıdır")
        if (v.get("color_transfer") or "") in ("smpte2084", "arib-std-b67") or m.get("hdr"):
            warn.append("HDR çəkiliş — SDR-ə çevrilir, rəng bir az fərqli ola bilər; telefonda HDR-i söndürmək tövsiyə olunur")
        head = min(w, h) / max(1, min(out_w, int(project.get("height") or out_w)))
        if head < 1.0:
            warn.append(f"ölçü {w}x{h} çıxışdan kiçikdir — böyüdülür, yumşalma olacaq")
        a = _audio_stats(src) if m.get("hasAudio") else None
        if a:
            if a["clipped"] > 50 or a["peakDb"] > -0.1:
                warn.append(f"səs partlayır (clipping: {a['clipped']} nümunə) — mikrofon çox yaxın/səs çox yüksək; düzəlmir, yalnız yumşaldılır")
            if a["speechDb"] < -32:
                warn.append(f"danışıq çox zəifdir ({a['speechDb']} dBFS) — gücləndiriləndə fon səsi də artacaq; voice-clean tövsiyə olunur")
        elif m.get("hasAudio") is False:
            warn.append("səs yoxdur")
        f = _frames_stats(src, float(m.get("duration") or 1))
        if f:
            if f["bright"] < 55:
                warn.append(f"görüntü qaranlıqdır (parlaqlıq {f['bright']}) — D (zəif işıq) rəngi və denoise")
            if f["bright"] > 215:
                warn.append(f"görüntü çox açıqdır (parlaqlıq {f['bright']}) — işıqlı yerlərdə detal itə bilər")
            if f["sharp"] < 0.45:
                warn.append(f"görüntü yumşaqdır/fokus zəifdir (kəskinlik {f['sharp']})")
            if f["motion"] > 12:
                warn.append(f"çox hərəkət/titrəmə (orta fərq {f['motion']}) — stabilizasiya yoxdur")
        items.append({"media": m["id"], "name": m["name"], "size": [w, h], "fps": round(avg or r, 3), "duration": m.get("duration"),
                      "audio": a, "frames": f, "headroom": round(head, 2), "warnings": warn})
    fpss = sorted({round(i["fps"]) for i in items if i["fps"]})
    if len(fpss) > 1:
        notes.append(f"fərqli kadr tezlikləri ({', '.join(map(str, fpss))} fps) — montaj bir fps-ə çevrilir; hərəkətdə kiçik qeyri-bərabərlik ola bilər")
    fr = [i["frames"] for i in items if i["frames"]]
    if len(fr) > 1:
        dw = max(x["warm"] for x in fr) - min(x["warm"] for x in fr)
        db = max(x["bright"] for x in fr) - min(x["bright"] for x in fr)
        if dw > 18:
            notes.append(f"kliplər arasında ağ balansı fərqi böyükdür (Δ {dw:.0f}) — rəng şablonu hamısına eyni tətbiq olunur, işıq bərabərləşdirilir")
        if db > 35:
            notes.append(f"kliplər arasında işıq fərqi böyükdür (Δ {db:.0f}) — matchExposure açıq qalsın")
    if items and max(i["headroom"] for i in items) >= 1.9:
        notes.append("keyfiyyət ehtiyatı ≥2x (məs. 4K → 1080): virtual multikamera üçün 3 plan ölçüsü (ümumi/orta/yaxın) mümkündür")
    return {"items": items, "notes": notes}


# ---------------------------------------------------------------------------
# Yekun yoxlama
# ---------------------------------------------------------------------------

def _filter_log(mp4: Path, vf: str | None = None, af: str | None = None) -> str:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4)]
    if vf:
        cmd += ["-vf", vf, "-an"]
    if af:
        cmd += ["-af", af, "-vn"]
    cmd += ["-f", "null", "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def black_frames(mp4: Path, min_d: float = 0.12) -> list[tuple[float, float]]:
    log = _filter_log(mp4, vf=f"blackdetect=d={min_d}:pic_th=0.97:pix_th=0.06")
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]


def frozen_frames(mp4: Path, min_d: float = 1.2) -> list[tuple[float, float]]:
    log = _filter_log(mp4, vf=f"freezedetect=n=-55dB:d={min_d}")
    st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", log)]
    return [(a, en[i] if i < len(en) else a + min_d) for i, a in enumerate(st)]


def loud_jumps(mp4: Path, over: float = 9.0) -> list[float]:
    """Qəfil səs sıçrayışı: anlıq səs (400 ms) adi səviyyədən (median) `over` LU yuxarı."""
    log = _filter_log(mp4, af="ebur128=peak=true")
    mom = [(float(t), float(mv)) for t, mv in re.findall(r"t:\s*([\d.]+)\s+TARGET:[-\d. ]+LUFS\s+M:\s*(-?[\d.]+)", log)]
    vals = [mv for _, mv in mom if mv > -60]
    if not vals:
        return []
    ref = float(np.median(vals))  # anlıq səviyyələrin medianı (ümumi səviyyə gücü sıçrayışın özündən təsirlənir)
    out, last = [], -9.0
    for t, mv in mom:
        if mv > ref + over and t - last > 1.0:
            out.append(round(t, 2))
            last = t
    return out


def true_peak(mp4: Path) -> float | None:
    log = _filter_log(mp4, af="ebur128=peak=true")
    m = re.findall(r"Peak:\s*(-?[\d.]+) dBFS", log)
    return float(m[-1]) if m else None


def reading_time(project: dict[str, Any]) -> list[dict[str, Any]]:
    """Ekran yazıları kifayət qədər qalırmı (sayğac və qısa nişanlar istisna)."""
    out = []
    for c in project.get("clips", []):
        if c.get("track") != "t1":
            continue
        txt = " ".join(str(c.get(k) or "") for k in ("text", "heading", "price", "note", "sub")).strip()
        items = c.get("items") or []
        txt += " " + " ".join(x if isinstance(x, str) else str((x or {}).get("text", "")) for x in items)
        n = len(re.findall(r"\w+", txt))
        if n <= 1 or c.get("type") == "badge":
            continue
        dur = float(c["srcOut"]) - float(c["srcIn"])
        need = max(READ_MIN, 0.4 + n / READ_WPS)
        if dur + 0.05 < need:
            out.append({"t": round(float(c.get("start") or 0), 2),
                        "what": f"yazı “{txt.strip()[:40]}” {dur:.1f} s qalır, oxumaq üçün ~{need:.1f} s lazımdır ({n} söz)"})
    return out


def final(project: dict[str, Any], mp4: Path, image_ranges: list[tuple[float, float]] | None = None,
          end_from: float | None = None) -> dict[str, Any]:
    """Yekun faylın ölçmə yoxlaması: {"checks": [...], "problems": [{"t","what"}]}."""
    checks, problems = [], []
    pr = _probe(mp4)
    v, a = pr["v"], pr["a"]
    W, H = int(project.get("width") or 0), int(project.get("height") or 0)
    tech = []
    if (int(v.get("width") or 0), int(v.get("height") or 0)) != (W, H):
        tech.append(f"ölçü {v.get('width')}x{v.get('height')} (gözlənilən {W}x{H})")
    if v.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
        tech.append(f"piksel formatı {v.get('pix_fmt')} (telefon üçün yuv420p)")
    if a and int(a.get("sample_rate") or 0) not in (44100, 48000):
        tech.append(f"səs tezliyi {a.get('sample_rate')} Hz")
    if tech:
        problems.append({"t": None, "what": "texniki: " + "; ".join(tech)})
    checks.append(f"texniki: {v.get('width')}x{v.get('height')} {v.get('pix_fmt')}, {_fps(v.get('avg_frame_rate')):.2f} fps"
                  + (f", səs {a.get('sample_rate')} Hz" if a else ", səs yoxdur"))
    skip = list(image_ranges or [])
    if end_from is not None:
        skip.append((end_from, 1e9))

    def outside(s: float, e: float) -> bool:
        return not any(s >= a0 - 0.1 and e <= b0 + 0.1 for a0, b0 in skip)
    bl = [(s, e) for s, e in black_frames(mp4) if outside(s, e)]
    for s, e in bl:
        problems.append({"t": round(s, 2), "what": f"qara kadr {e - s:.2f} s"})
    checks.append(f"qara kadr yoxlaması ({len(bl)} yer)")
    fz = [(s, e) for s, e in frozen_frames(mp4) if outside(s, e)]
    for s, e in fz:
        problems.append({"t": round(s, 2), "what": f"görüntü {e - s:.1f} s donub (hərəkətsiz) — klip qısa qalıb və ya şəkil kimi görünür; yoxla"})
    checks.append(f"donmuş kadr yoxlaması ({len(fz)} yer)")
    if a:
        tp = true_peak(mp4)
        if tp is not None:
            checks.append(f"səs piki {tp:.1f} dBFS")
            if tp > -0.5:
                problems.append({"t": None, "what": f"səs piki {tp:.1f} dBFS — partlama riski (limitləyici yoxlanmalıdır)"})
        for t in loud_jumps(mp4):
            problems.append({"t": t, "what": "qəfil səs sıçrayışı (adi səviyyədən 9 LU yuxarı) — dinləyib yoxla"})
        checks.append("qəfil səs sıçrayışı yoxlaması")
    rt = reading_time(project)
    problems += rt
    checks.append(f"ekran yazılarının oxunma müddəti ({len(rt)} qısa)")
    return {"checks": checks, "problems": problems}
