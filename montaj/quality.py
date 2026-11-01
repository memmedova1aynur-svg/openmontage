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
        prev_c = vclips[i - 1] if i else None
        next_c = vclips[i + 1] if i + 1 < len(vclips) else None
        for kind, t, tl in (("in", c["srcIn"], c["start"]), ("out", c["srcOut"], c["start"] + c["dur"])):
            if (kind == "in" and t < 0.05) or (kind == "out" and t > dur_src - 0.05):
                continue  # mənbənin öz başı/sonu — kəsim deyil
            nb = prev_c if kind == "in" else next_c  # davamlı bölünmə (plan ölçüsü, danışana keçid) — səs kəsilmir
            if nb and nb.get("media") == c.get("media") and abs((nb["srcOut"] if kind == "in" else nb["srcIn"]) - t) < 0.02:
                continue
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
    for k, c in enumerate(vclips[1:], 1):
        pc = vclips[k - 1]
        if pc.get("media") == c.get("media") and abs(pc["srcOut"] - c["srcIn"]) < 0.02:
            continue  # davamlı bölünmə — səsdə kəsim yoxdur
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
        rep["unverified"].append("yekun səsin yenidən tanınması (" + ("söndürülüb: --no-asr" if not asr else "Whisper yoxdur") + ")")
    import tempfile

    try:
        lay = layout_check(project, project_dir, Path(tempfile.mkdtemp(prefix="montaj_layout_")))
        rep["checks"].append("kartlar/altyazı: üzü örtmə və Instagram interfeysi zonası yoxlandı")
        rep["problems"] += lay
    except Exception as e:  # noqa: BLE001
        rep["unverified"].append(f"kart/üz/təhlükəsiz zona yoxlaması alınmadı: {str(e)[:120]}")
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


# ---------------------------------------------------------------------------
# Təkrar / yarımçıq cümlələr (dublyaj)
# ---------------------------------------------------------------------------

def sentences(words: list[dict[str, Any]], gap: float = 0.6) -> list[dict[str, Any]]:
    """Söz vaxtlarından cümlələr: nöqtə/sual/nida və ya uzun pauza ilə bölünür."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        end_punct = w["w"].rstrip().endswith((".", "?", "!", "…"))
        nxt_gap = (words[i + 1]["s"] - w["e"]) if i + 1 < len(words) else 9
        if end_punct or nxt_gap >= gap:
            out.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur, "text": " ".join(x["w"] for x in cur)})
            cur = []
    if cur:
        out.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur, "text": " ".join(x["w"] for x in cur)})
    return out


def find_retakes(words: list[dict[str, Any]], window: int = 3, min_ratio: float = 0.62) -> list[dict[str, Any]]:
    """Ardıcıl təkrarlanan cümlələr (sonrakı cəhd adətən tamdır): əvvəlki cəhdin çıxarılması təklif olunur.
    Növlər: "repeat" — oxşar cümlə yenidən deyilib; "restart" — cümlə yarımçıq qalıb, eyni sözlərlə yenidən başlayıb."""
    norm = transcribe.norm_word
    ss = sentences(words)
    res, used = [], set()
    for i, a in enumerate(ss):
        if i in used:
            continue
        aw = [norm(w["w"]) for w in a["words"] if norm(w["w"])]
        if len(aw) < 2:
            continue
        for j in range(i + 1, min(len(ss), i + 1 + window)):
            bw = [norm(w["w"]) for w in ss[j]["words"] if norm(w["w"])]
            if len(bw) < 2:
                continue
            ratio = difflib.SequenceMatcher(a=aw, b=bw, autojunk=False).ratio()
            k = 0
            while k < min(len(aw), len(bw)) and aw[k] == bw[k]:
                k += 1
            restart = k >= 2 and len(aw) <= len(bw)  # eyni başlanğıc, sonra daha tam variant
            if ratio >= min_ratio or restart:
                res.append({"kind": "restart" if restart and ratio < min_ratio else "repeat", "ratio": round(ratio, 2),
                            "drop": {"s": a["s"], "e": ss[j]["s"], "text": a["text"]},
                            "keep": {"s": ss[j]["s"], "e": ss[j]["e"], "text": ss[j]["text"]}})
                used.update(range(i, j))
                break
    return res


# ---------------------------------------------------------------------------
# Kart üzü örtürmü / Instagram təhlükəsiz zonası
# ---------------------------------------------------------------------------

# Reels interfeysi (normallaşdırılmış 9:16): yuxarıda hesab adı, aşağıda caption/səs, sağda düymələr
SAFE_ZONES = {"yuxarı (hesab adı)": (0.0, 0.0, 1.0, 0.08), "aşağı (caption, musiqi)": (0.0, 0.86, 1.0, 1.0),
              "sağ (bəyən/şərh düymələri)": (0.88, 0.45, 1.0, 0.90)}


def _inter(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h


def _alpha_box(png: str, W: int, H: int, cx: float, cy: float) -> tuple[float, float, float, float] | None:
    from PIL import Image

    im = Image.open(png)
    bb = im.getchannel("A").getbbox() if im.mode == "RGBA" else (0, 0, im.width, im.height)
    if not bb:
        return None
    x0, y0 = cx * W - im.width / 2, cy * H - im.height / 2
    return ((x0 + bb[0]) / W, (y0 + bb[1]) / H, (x0 + bb[2]) / W, (y0 + bb[3]) / H)


def _face_in_output(project_dir: Path, media: dict[str, Any], clip: dict[str, Any], src_t: float) -> tuple[float, ...] | None:
    from montaj import reframe

    smp = reframe.detect_faces(project_dir / media["file"], src_t, src_t + 0.5, step=0.5)
    fs = [f for x in smp for f in x["faces"][:1]]
    if not fs:
        return None
    f = max(fs, key=lambda z: z["w"] * z["h"])
    box = (f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])
    fr = clip.get("frame") or {}
    if fr.get("mode") in ("auto", "manual") and fr.get("keys"):
        w, h = float(fr.get("baseW", 1)) * float(fr.get("s", 1)), float(fr.get("baseH", 1)) * float(fr.get("s", 1))
        k = fr["keys"][0]
        cx = min(max(float(k["cx"]), w / 2), 1 - w / 2)
        cy = min(max(float(k["cy"]), h / 2), 1 - h / 2)
        x0, y0 = cx - w / 2, cy - h / 2
        box = ((box[0] - x0) / w, (box[1] - y0) / h, (box[2] - x0) / w, (box[3] - y0) / h)
    return box


def layout_check(project: dict[str, Any], project_dir: Path, workdir: Path) -> list[dict[str, Any]]:
    """Kartlar/başlıqlar üzü örtürmü və mətn Reels interfeysi zonasına düşürmü (yekun kadr koordinatlarında)."""
    from montaj import graphics as G
    from montaj.render import output_dims, render_plan

    plan = render_plan(project)
    W, H = output_dims(project)
    media = {m["id"]: m for m in project["media"]}
    items, meta = [], {}
    caps = 0
    for t in plan["text"]:
        c = t["clip"]
        if not G.is_graphic(c):
            continue
        if c["type"] == "caption":
            caps += 1
            if caps > 3:  # altyazılar eyni yerdədir — bir neçə nümunə kifayətdir
                continue
        pts = G.state_points(c)
        tl = pts[-1] if len(pts) > 1 else (float(c["srcOut"]) - float(c["srcIn"])) / 2
        name = f"chk_{c['id']}"
        items.append((name, dict(c, _start=t["start"]), tl))
        meta[name] = (c, t["start"] + min(tl + 0.05, float(c["srcOut"]) - float(c["srcIn"]) - 0.05), t["start"], t["end"])
    if not items:
        return []
    workdir.mkdir(parents=True, exist_ok=True)
    rast = G.rasterize(items, W, H, (project.get("brand") or {}).get("theme"), workdir)
    out = []
    covers = [(o["start"], o["start"] + o["dur"]) for o in plan["overlay"] if o["clip"].get("mode") != "pip"]
    boxes = {}
    for name, (c, t_abs, a0, b0) in meta.items():
        info = rast.get(name)
        if info:
            bx = _alpha_box(info["file"], W, H, *G.pos(c))
            if bx:
                boxes[name] = (c, a0, b0, bx)
    # qrafikalar bir-birini örtürmü (eyni anda görünənlər); altyazı bir nümunə ilə bütün vaxt üçün yoxlanır
    cap_box = next((v[3] for v in boxes.values() if v[0]["type"] == "caption"), None)
    gl = [(n, v) for n, v in boxes.items() if v[0]["type"] != "caption"]
    for i, (n1, (c1, a1, b1, x1)) in enumerate(gl):
        others = [(c2, a2, b2, x2) for _n2, (c2, a2, b2, x2) in gl[i + 1:]]
        if cap_box and project.get("subtitles", {}).get("enabled"):
            others.append(({"type": "caption", "text": "altyazı"}, a1, b1, cap_box))
        for c2, a2, b2, x2 in others:
            if min(b1, b2) - max(a1, a2) > 0.2 and _inter(x1, x2) / max(1e-6, min((x1[2] - x1[0]) * (x1[3] - x1[1]), (x2[2] - x2[0]) * (x2[3] - x2[1]))) > 0.08:
                lab2 = "altyazı" if c2["type"] == "caption" else f"{c2['type']} “{str(c2.get('text') or c2.get('heading') or c2.get('price') or '')[:24]}”"
                out.append({"t": round(max(a1, a2), 2), "what": f"{c1['type']} “{str(c1.get('text') or c1.get('heading') or c1.get('price') or '')[:24]}” və {lab2} üst-üstə düşür"})
    for name, (c, t_abs, _a0, _b0) in meta.items():
        if name not in boxes:
            continue
        box = boxes[name][3]
        label = "altyazı" if c["type"] == "caption" else f"{c['type']} “{str(c.get('text') or c.get('heading') or '')[:30]}”"
        area = max(1e-6, (box[2] - box[0]) * (box[3] - box[1]))
        for zname, z in SAFE_ZONES.items():
            if _inter(box, z) / area > 0.04:
                out.append({"t": round(t_abs, 2), "what": f"{label} Instagram interfeysi zonasına düşür: {zname}"})
        if any(a <= t_abs < b for a, b in covers):
            continue  # B-roll üzü onsuz da örtür
        v = next((it for it in plan["video"] if it["start"] <= t_abs < it["start"] + it["dur"]), None)
        if not v or v["clip"].get("broll"):
            continue
        m = media.get(v["clip"].get("media"))
        if not m or not m.get("hasVideo") or m.get("isImage"):
            continue
        face = _face_in_output(project_dir, m, v["clip"], float(v["clip"]["srcIn"]) + (t_abs - v["start"]))
        if face:
            fx = (face[2] - face[0]) * 0.1
            fbox = (face[0] - fx, face[1] - (face[3] - face[1]) * 0.2, face[2] + fx, face[3] + (face[3] - face[1]) * 0.1)
            farea = max(1e-6, (fbox[2] - fbox[0]) * (fbox[3] - fbox[1]))
            ov = _inter(box, fbox) / farea
            if ov > 0.12:
                out.append({"t": round(t_abs, 2), "what": f"{label} üzü {ov * 100:.0f}% örtür — yerini dəyiş"})
    return out


CAPTION_TOP = 0.715  # altyazının yuxarı kənarı (standart y=0.74)
EST_H = {"offer": 0.235, "cta": 0.215, "badge": 0.07, "card": 0.2, "list": 0.25, "title": 0.08, "emphasis": 0.07}


def place_below_face(project_dir: Path, media: dict[str, Any], frame: dict[str, Any] | None, src_t: float, kind: str,
                     default_y: float) -> tuple[float, float, str]:
    """Kartın yeri (mərkəz y) və ölçü əmsalı: üzün (çənənin) altında, altyazının üstündə; yer azdırsa kart kiçilir
    (≥65%); yenə sığmırsa başın üstünə. Nəticə: (y, scale, izah)."""
    h = EST_H.get(kind, 0.15)
    face = _face_in_output(project_dir, media, {"frame": frame} if frame else {}, src_t)
    if not face:
        return default_y, 1.0, "üz tapılmadı — standart yer"
    fh = face[3] - face[1]
    chin = face[3] + fh * 0.12
    band = CAPTION_TOP - 0.005 - (chin + 0.01)  # çənə ilə altyazı arasındakı boş zolaq
    if band >= h:
        y = max(default_y, chin + 0.01 + h / 2)
        return round(min(y, CAPTION_TOP - 0.005 - h / 2), 3), 1.0, "üzün altında"
    if band >= 0.65 * h:
        sc = band / h
        return round(chin + 0.01 + band / 2, 3), round(sc, 2), f"üzün altında, kart {sc * 100:.0f}% ölçüdə"
    head_top = face[1] - fh * 0.3  # saç
    room = head_top - 0.01 - 0.09  # Instagram yuxarı zonasından aşağı
    if room >= 0.65 * h:
        sc = min(1.0, room / h)
        return round(head_top - 0.01 - h * sc / 2, 3), round(sc, 2), "başın üstündə" + (f", kart {sc * 100:.0f}% ölçüdə" if sc < 1 else "")
    return default_y, 1.0, "boş yer tapılmadı — verify ilə yoxla"
