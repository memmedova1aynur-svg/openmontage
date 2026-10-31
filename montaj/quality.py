"""Montaj keyfiyyəti: təhlükəsiz kəsim nöqtəsi, yekun render yoxlaması, şübhəli sözlər,
kadrlar arası işıq uyğunlaşdırması və musiqi dinləmə nümunələri.

Qaydalar (istifadəçi tələbi):
* Kəsim nöqtəsi yalnız Whisper-ə yox, orijinal səsin enerjisinə əsaslanır; söz içinə düşmür.
* Şübhəli sərhəddə daha çox orijinal material saxlanılır (kəsim çölə doğru sürüşür).
* Yoxlanılmayan hissə "yoxlanılıb" kimi göstərilmir: hesabatda hər yoxlamanın növü yazılır.
"""

from __future__ import annotations

import difflib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from montaj import media as mediautil
from montaj import transcribe

SR = 16000
HOP = 0.01  # 10 ms çərçivə


def frame_rms(audio: np.ndarray, sr: int = SR, hop: float = HOP) -> np.ndarray:
    n = max(1, int(sr * hop))
    k = len(audio) // n
    if k == 0:
        return np.zeros(0)
    x = audio[: k * n].astype(np.float64).reshape(k, n)
    return np.sqrt((x * x).mean(axis=1))


def _db(x: float) -> float:
    return 20 * np.log10(max(x, 1e-6))


def speech_level(rms: np.ndarray) -> float:
    """Danışığın tipik səviyyəsi (səsli çərçivələrin medianı)."""
    v = rms[rms > np.percentile(rms, 40)] if len(rms) else rms
    return float(np.median(v)) if len(v) else 1e-3


def safe_boundary(rms: np.ndarray, t: float, kind: str, words: list[dict[str, Any]],
                  ref: float, window: float = 0.15) -> tuple[float, bool]:
    """Kəsim nöqtəsini ən sakit yerə çəkir.

    kind="out": saxlanılan hissənin sonu (daha gec = daha çox material saxlanılır);
    kind="in":  saxlanılan hissənin başlanğıcı (daha tez = daha çox material).
    Söz içinə (±30 ms) düşən çərçivələr seçilmir. Sakit yer tapılmırsa nöqtə material
    saxlanılan tərəfə sürüşür və ok=False qaytarılır (şübhəli sərhəd).
    """
    lo, hi = max(0, int((t - window) / HOP)), min(len(rms) - 1, int((t + window) / HOP))
    if hi <= lo:
        return t, False
    inside = [(w["s"] - 0.03, w["e"] + 0.03) for w in words if w["e"] > t - window - 0.1 and w["s"] < t + window + 0.1]
    best, best_v = None, None
    for i in range(lo, hi + 1):
        x = i * HOP
        if any(a < x < b for a, b in inside):
            continue
        v = float(rms[i])
        # bərabər sakitlikdə material saxlayan tərəf üstündür
        bias = (x - t) if kind == "in" else (t - x)
        score = v + 1e-4 * bias
        if best_v is None or score < best_v:
            best, best_v = x, score
    quiet = best is not None and float(rms[int(best / HOP)]) < 0.12 * ref  # ~ -18 dB danışıqdan aşağı
    if not quiet:
        x = t + window if kind == "out" else t - window
        x = _snap_out(x, words, kind)
        return round(max(0.0, x), 3), False
    return round(best, 3), True


def _snap_out(x: float, words: list[dict[str, Any]], kind: str) -> float:
    for w in words:
        if w["s"] - 0.03 < x < w["e"] + 0.03:
            return w["e"] + 0.05 if kind == "out" else w["s"] - 0.05
    return x


# ---------------------------------------------------------------------------
# Yekun render yoxlaması
# ---------------------------------------------------------------------------

def _stream_durations(mp4: Path) -> dict[str, float]:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(mp4)],
                         capture_output=True, text=True, check=True).stdout
    return {s["codec_type"]: float(s.get("duration") or 0) for s in json.loads(out)["streams"]}


def verify(project: dict[str, Any], project_dir: Path, mp4: Path, analyses: dict[str, dict[str, Any]],
           asr: bool = True) -> dict[str, Any]:
    """Kəsim sərhədləri, səs-görüntü uzunluğu, kliklər və (asr=True) yekun səsin yenidən tanınması."""
    from montaj.render import render_plan

    rep: dict[str, Any] = {"mp4": str(mp4), "checks": [], "problems": [], "unverified": []}
    d = _stream_durations(mp4)
    fps = float(project.get("fps") or 30)
    diff = abs(d.get("video", 0) - d.get("audio", 0))
    rep["checks"].append(f"səs/görüntü uzunluğu: video {d.get('video', 0):.3f} s, səs {d.get('audio', 0):.3f} s")
    if diff > 1.5 / fps + 0.03:
        rep["problems"].append({"t": None, "what": f"səs və görüntü uzunluğu {diff:.2f} s fərqlidir"})

    plan = render_plan(project)
    # zaman xəttindəki video kliplər: mənbə aralığı + yekun videoda başlanğıc/müddət
    vclips = [{**it["clip"], "start": it["start"], "dur": it["dur"]} for it in plan["video"]]
    media = {m["id"]: m for m in project["media"]}
    cache: dict[str, tuple[np.ndarray, float]] = {}

    def rms_of(mid: str) -> tuple[np.ndarray, float]:
        if mid not in cache:
            r = frame_rms(mediautil.read_mono(project_dir / media[mid]["file"], SR))
            cache[mid] = (r, speech_level(r))
        return cache[mid]

    cuts = 0
    for i, c in enumerate(vclips):
        m = media.get(c.get("media"))
        if not m or not m.get("hasAudio") or m.get("isImage"):
            continue
        rms, ref = rms_of(m["id"])
        words = (analyses.get(m["id"]) or {}).get("words") or []
        dur_src = float(m.get("duration") or 0)
        for kind, t, tl in (("in", c["srcIn"], c["start"]), ("out", c["srcOut"], c["start"] + c["dur"])):
            if (kind == "in" and t < 0.05) or (kind == "out" and t > dur_src - 0.05):
                continue  # mənbənin öz başı/sonu — kəsim deyil
            cuts += 1
            j = int(t / HOP)
            seg = rms[max(0, j - 3): j] if kind == "out" else rms[j: j + 3]
            level = float(seg.mean()) if len(seg) else 0.0
            in_word = next((w for w in words if w["s"] + 0.02 < t < w["e"] - 0.02), None)
            if in_word:
                rep["problems"].append({"t": round(tl, 2), "what": f"kəsim “{in_word['w']}” sözünün içinə düşür"})
            elif level > 0.35 * ref:
                rep["problems"].append({"t": round(tl, 2), "what": f"kəsim anında səs davam edir ({_db(level / ref):+.0f} dB) — sözün sonu/başı kəsilmiş ola bilər"})
    rep["checks"].append(f"{cuts} kəsim sərhədi orijinal səsin enerjisi və söz vaxtları ilə yoxlandı")

    # kliklər: yekun səsdə sərhəd ətrafında qəfil sıçrayış
    fin = mediautil.read_mono(mp4, SR)
    clicks = 0
    for c in vclips[1:]:
        j = int(c["start"] * SR)
        if 64 < j < len(fin) - 64:
            jump = float(np.abs(np.diff(fin[j - 32: j + 32])).max())
            around = float(np.abs(np.diff(fin[j - 2000: j - 200])).mean()) + 1e-4 if j > 2000 else 1e-3
            if jump > 0.25 and jump > 30 * around:
                clicks += 1
                rep["problems"].append({"t": round(c["start"], 2), "what": "kəsimdə klik səsi ola bilər"})
    rep["checks"].append(f"kəsimlərdə klik yoxlaması ({len(vclips) - 1} yer)")

    if asr and transcribe.available()["installed"]:
        expected: list[str] = []
        for c in vclips:
            ws = (analyses.get(c.get("media")) or {}).get("words") or []
            expected += [w["w"] for w in ws if w["s"] >= c["srcIn"] - 0.02 and w["e"] <= c["srcOut"] + 0.02]
        got = transcribe.transcribe(mp4, 0.0, d.get("audio") or d.get("video") or 0)["words"]
        norm = transcribe.norm_word
        ratio = difflib.SequenceMatcher(a=[norm(x) for x in expected], b=[norm(w["w"]) for w in got], autojunk=False).ratio()
        models = {(analyses.get(c.get("media")) or {}).get("model") for c in vclips} - {None}
        note = f" (analiz modeli {', '.join(models)} — fərqli modeldir, ümumi faiz təxminidir)" if models and models != {transcribe.DEFAULT_MODEL} else ""
        rep["checks"].append(f"yekun səs yenidən tanındı ({transcribe.DEFAULT_MODEL}): ümumi uyğunluq {ratio * 100:.0f}%{note}")

        def heard(word: str, t: float) -> bool:
            a = norm(word)
            for g in got:
                if abs(g["s"] - t) <= 0.8:
                    b = norm(g["w"])
                    if a and b and (a in b or b in a or difflib.SequenceMatcher(a=a, b=b).ratio() >= 0.6):
                        return True
            return False

        edge = 0
        for c in vclips:  # yalnız kəsim yanındakı sözlər: hər klipin ilk və son sözü yekun səsdə eşidilirmi
            m = media.get(c.get("media")) or {}
            ws = [w for w in ((analyses.get(c.get("media")) or {}).get("words") or [])
                  if w["s"] >= c["srcIn"] - 0.02 and w["e"] <= c["srcOut"] + 0.02]
            if not ws:
                continue
            checks = []
            if c["srcIn"] > 0.05:
                checks.append(ws[0])
            if c["srcOut"] < float(m.get("duration") or 0) - 0.05:
                checks.append(ws[-1])
            for w in checks:
                edge += 1
                te = c["start"] + (w["s"] - c["srcIn"])
                if not heard(w["w"], te):
                    rep["problems"].append({"t": round(te, 2), "what": f"kəsim yanındakı “{w['w']}” sözü yekun səsdə tanınmadı — dinləyib yoxlayın"})
        rep["checks"].append(f"kəsim yanındakı {edge} söz yekun səsdə axtarıldı")
    else:
        rep["unverified"].append("yekun səsin yenidən tanınması (Whisper yoxdur)")
    rep["unverified"].append("səs qulaqla dinlənilməyib — yoxlama ölçmə ilədir")
    return rep


# ---------------------------------------------------------------------------
# Şübhəli sözlər
# ---------------------------------------------------------------------------

def suspicious_words(project: dict[str, Any], analyses: dict[str, dict[str, Any]], threshold: float = 0.6) -> list[dict[str, Any]]:
    """Montajda qalan, Whisper-in əmin olmadığı sözlər (zaman xəttində vaxtı ilə). Düzəldilmişlər çıxarılır."""
    from montaj.render import render_plan

    fixed = {transcribe.norm_word(c["from"]) for c in ((project.get("subtitles") or {}).get("corrections") or [])}
    plan = render_plan(project)
    # əl ilə düzəldilmiş altyazılar: həmin vaxtda söz artıq mətndə yoxdursa — düzəldilib
    manual = [(t["start"], t["end"], " ".join(transcribe.norm_word(x) for x in str(t["clip"].get("text", "")).split()))
              for t in plan["text"] if t["clip"].get("track") == "c1" and t["clip"].get("manual")]
    out = []
    for it in plan["video"]:
        c = {**it["clip"], "start": it["start"]}
        ws = (analyses.get(c.get("media")) or {}).get("words") or []
        kept = [w for w in ws if w["s"] >= c["srcIn"] - 0.02 and w["e"] <= c["srcOut"] + 0.02]
        for i, w in enumerate(kept):
            nw = transcribe.norm_word(w["w"])
            t = round(c["start"] + w["s"] - c["srcIn"], 2)
            if float(w.get("p", 1)) >= threshold or nw in fixed:
                continue
            if any(a - 0.05 <= t <= b + 0.05 and nw not in txt.split() for a, b, txt in manual):
                continue
            ctx = " ".join(x["w"] for x in kept[max(0, i - 3): i + 4])
            out.append({"t": t, "word": w["w"], "p": w.get("p"), "context": ctx})
    return out


# ---------------------------------------------------------------------------
# İşıq uyğunlaşdırması (fərqli işıqlanan kadrlar)
# ---------------------------------------------------------------------------

def mean_luma(src: Path, t: float) -> float | None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", str(src), "-frames:v", "1",
                        "-vf", "scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if "YAVG=" in line:
            return float(line.split("=")[1])
    return None


def exposure_offsets(clips: list[dict[str, Any]], media: dict[str, dict[str, Any]], project_dir: Path,
                     max_shift: float = 0.04) -> dict[str, float]:
    """Hər video klipin orta işığını layihənin medianına yaxınlaşdıran kiçik parlaqlıq düzəlişi."""
    lum = {}
    for c in clips:
        m = media.get(c.get("media"))
        if m and m.get("hasVideo") and not m.get("isImage"):
            y = mean_luma(project_dir / m["file"], (c["srcIn"] + c["srcOut"]) / 2)
            if y is not None:
                lum[c["id"]] = y
    if len(lum) < 2:
        return {}
    target = float(np.median(list(lum.values())))
    out = {}
    for cid, y in lum.items():
        if abs(y - target) >= 4:  # 8-bit vahiddə görünən fərq
            out[cid] = round(float(np.clip((target - y) / 255 * 0.8, -max_shift, max_shift)), 3)
    return out


# ---------------------------------------------------------------------------
# Musiqi dinləmə nümunəsi
# ---------------------------------------------------------------------------

def music_preview(speech_src: Path, music: Path, out: Path, seconds: float = 20, volume: float = 0.12,
                  start: float = 0.0) -> Path:
    """Danışığın ilk saniyələri + musiqi (danışıqda azalır, yumşaq giriş/çıxış) — .m4a."""
    fo = max(0.0, seconds - 1.5)
    flt = (f"[0:a]atrim=0:{seconds},asetpts=N/SR/TB,aformat=channel_layouts=stereo,asplit=2[sp][key];"
           f"[1:a]atrim={start}:{start + seconds},asetpts=N/SR/TB,volume={volume},afade=t=in:d=1.2,afade=t=out:st={fo}:d=1.5,"
           f"aformat=channel_layouts=stereo[mu];"
           f"[mu][key]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=400[duck];"
           f"[sp][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[out]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(speech_src), "-i", str(music), "-filter_complex", flt,
                    "-map", "[out]", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    return out
