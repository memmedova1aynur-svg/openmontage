"""Materialın analizi və söz sərhədinə görə təhlükəsiz hissələr.

Qaydalar:
  * Kəsim nöqtəsi YALNIZ iki söz arasındakı boşluqda ola bilər (söz/heca yarıda kəsilmir).
  * Qısa pauzalar, nəfəs və vurğu səssizliyi (< `long_pause`) hissənin içində qalır.
  * Uzun pauza silinəndə hər tərəfdə `breath` qədər hava saxlanılır.
  * Transkript yoxdursa, yalnız uzun səssizliklər (ffmpeg) əsasında bölünür.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from montaj import media as mediautil
from montaj import transcribe
from montaj.errors import UserError

CUT_MODES = ("keep", "suggest", "auto")
IMAGE_SECONDS = 3.0


def analysis_path(project_dir: Path, mid: str) -> Path:
    return project_dir / "analysis" / f"{mid}.json"


def analyze_media(project_dir: Path, m: dict[str, Any], language: str = "az",
                  progress=None) -> dict[str, Any]:
    """Transkript (varsa) + səssizlik. Nəticə diskdə keşlənir."""
    out = analysis_path(project_dir, m["id"])
    if out.is_file():
        return json.loads(out.read_text(encoding="utf-8"))
    res: dict[str, Any] = {"mediaId": m["id"], "duration": m["duration"], "words": [], "silences": [],
                           "transcribed": False, "language": None}
    if m.get("isImage"):
        res["duration"] = IMAGE_SECONDS
    elif m.get("hasAudio"):
        src = project_dir / m["file"]
        res["silences"] = mediautil.detect_silence(src, 0, float(m["duration"]), -35, 0.5)
        if progress:
            progress(0.2)
        if transcribe.available()["installed"]:
            try:
                t = transcribe.transcribe(src, 0.0, float(m["duration"]), language)
                res.update(words=t["words"], transcribed=True, language=t["language"],
                           languageProbability=t["languageProbability"], text=t["text"], model=t["model"])
            except Exception as e:  # noqa: BLE001
                res["transcribeError"] = str(e)[-300:]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return res


def word_gaps(words: list[dict[str, Any]]) -> list[tuple[float, float]]:
    """Ardıcıl sözlər arasındakı boşluqlar — yeganə təhlükəsiz kəsim yerləri."""
    return [(words[i]["e"], words[i + 1]["s"]) for i in range(len(words) - 1)]


def drop_hallucinated(words: list[dict[str, Any]], silences: list[tuple[float, float]]) -> list[dict[str, Any]]:
    """Əsasən səssiz intervala düşən “sözləri” atır.

    Whisper səssizlikdə və ya musiqidə söz uydura bilir; ffmpeg səssizlik ölçüsü
    ilə çarpaz yoxlama bunu azaldır.
    """
    out = []
    for w in words:
        s, e = w["s"], w["e"]
        for a, b in silences:
            ov = max(0.0, min(e, b) - max(s, a))
            if ov <= 0:
                continue
            if ov >= 0.6 * (e - s):
                s = e  # əsasən səssizlikdə — uydurma söz sayılır, atılır
                break
            # qismən üst-üstə düşmə: sözün sərhədi qorunur (heca kəsilməsin deyə ehtiyatlı tərəf)
        if e - s > 0.02:
            out.append({**w, "s": round(s, 3), "e": round(e, 3)})
    return out


def segments_from_words(words: list[dict[str, Any]], dur: float, long_pause: float = 1.2,
                        breath: float = 0.25, drop_fillers: bool = False,
                        silences: list[tuple[float, float]] | None = None) -> list[dict[str, Any]]:
    """Sözləri uzun pauzalarda hissələrə bölür. Hər hissə [ilk söz - nəfəs, son söz + nəfəs]."""
    ws = [w for w in words if w["e"] > w["s"]]
    if silences:
        ws = drop_hallucinated(ws, silences)
    if drop_fillers:
        ws = [w for w in ws if transcribe.norm_word(w["w"]) not in transcribe.AZ_FILLERS]
    if not ws:
        return []
    groups: list[list[dict[str, Any]]] = [[ws[0]]]
    for prev, w in zip(ws, ws[1:]):
        gap = w["s"] - prev["e"]
        filler_between = drop_fillers and any(
            prev["e"] <= x["s"] and x["e"] <= w["s"] and transcribe.norm_word(x["w"]) in transcribe.AZ_FILLERS
            for x in words)
        if gap >= long_pause or (filler_between and gap > 0.35):
            groups.append([w])
        else:
            groups[-1].append(w)
    segs = []
    for i, g in enumerate(groups):
        lo_lim = groups[i - 1][-1]["e"] if i else 0.0
        hi_lim = groups[i + 1][0]["s"] if i + 1 < len(groups) else dur
        # nəfəs payı qonşu hissənin sözünə girməsin: ən çoxu boşluğun ortasına qədər
        a = max(g[0]["s"] - breath, (lo_lim + g[0]["s"]) / 2 if i else 0.0, 0.0)
        b = min(g[-1]["e"] + breath, (g[-1]["e"] + hi_lim) / 2 if i + 1 < len(groups) else dur)
        segs.append({"srcIn": round(a, 3), "srcOut": round(b, 3),
                     "text": " ".join(w["w"] for w in g).strip(),
                     "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in g]})
    return segs


def segments_from_silence(silences: list[tuple[float, float]], dur: float, long_pause: float = 1.2,
                          breath: float = 0.25) -> list[dict[str, Any]]:
    keep = mediautil.keep_ranges(0.0, dur, [s for s in silences if s[1] - s[0] >= long_pause],
                                 pad=breath, min_keep=0.3)
    return [{"srcIn": a, "srcOut": b, "text": "", "words": []} for a, b in keep]


def _snap_out_of_words(t: float, words: list[dict[str, Any]], direction: int, pad: float = 0.06) -> float:
    """Kəsim nöqtəsi sözün içinə düşürsə, sözün kənarına (çölə) çəkilir."""
    for w in words:
        if w["s"] < t < w["e"]:
            return w["s"] - pad if direction < 0 else w["e"] + pad
    return t


def segments_safe(dur: float, silences: list[tuple[float, float]], words: list[dict[str, Any]],
                  long_pause: float, breath: float = 0.25, drop_fillers: bool = False) -> list[dict[str, Any]]:
    """Səsli hissələri saxlayır, yalnız uzun səssizlikləri (və avtomatik rejimdə doldurucu sözləri) çıxarır.

    * Material (musiqi, gülüş, tanınmayan danışıq) transkriptdə olmasa da atılmır.
    * Kəsim nöqtələri söz sərhədinə çəkilir — söz/heca yarıda kəsilmir.
    """
    words = drop_hallucinated(words, silences) if silences else list(words)
    remove = [(a, b) for a, b in silences if b - a >= long_pause]
    if not silences and words:
        # səs-küylü yazı: ffmpeg səssizlik tapmırsa, uzun söz boşluqlarından istifadə et
        remove = [(a, b) for a, b in word_gaps(words) if b - a >= long_pause]
    if drop_fillers:
        for w in words:
            if transcribe.norm_word(w["w"]) in transcribe.AZ_FILLERS:
                remove.append((w["s"] - 0.02, w["e"] + 0.02))
    keep = mediautil.keep_ranges(0.0, dur, sorted(remove), pad=breath, min_keep=0.3)
    real_words = [w for w in words if not (drop_fillers and transcribe.norm_word(w["w"]) in transcribe.AZ_FILLERS)]
    segs = []
    for a, b in keep:
        a2 = max(0.0, _snap_out_of_words(a, real_words, -1))
        b2 = min(dur, _snap_out_of_words(b, real_words, +1))
        ws = [w for w in real_words if w["s"] >= a2 - 1e-6 and w["e"] <= b2 + 1e-6]
        segs.append({"srcIn": round(a2, 3), "srcOut": round(b2, 3), "text": " ".join(w["w"] for w in ws).strip(),
                     "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in ws]})
    return segs


def candidate_segments(m: dict[str, Any], an: dict[str, Any], cut_mode: str) -> list[dict[str, Any]]:
    """Kəsim rejiminə görə namizəd hissələr (kartlar üçün)."""
    if cut_mode not in CUT_MODES:
        raise UserError("Naməlum kəsim rejimi.", "Kəsim rejimini yenidən seçin.")
    dur = float(an.get("duration") or m["duration"])
    if m.get("isImage"):
        segs = [{"srcIn": 0.0, "srcOut": IMAGE_SECONDS, "text": "", "words": []}]
    elif m.get("hasAudio"):
        segs = segments_safe(dur, [tuple(x) for x in an.get("silences", [])], an.get("words") or [],
                             long_pause=1.2 if cut_mode != "auto" else 0.8, drop_fillers=cut_mode == "auto")
    else:
        segs = []
    if cut_mode == "keep" or not segs:
        # Olduğu kimi: hissələr bütün materialı boşluqsuz örtür (bölmə yalnız storyboard üçün)
        if not segs:
            segs = [{"srcIn": 0.0, "srcOut": round(dur, 3), "text": "", "words": an.get("words", [])}]
        else:
            for i, sg in enumerate(segs):
                sg["srcIn"] = 0.0 if i == 0 else segs[i - 1]["srcOut"]
            segs[-1]["srcOut"] = round(dur, 3)
            allw = an.get("words") or []
            for sg in segs:
                ws = [w for w in allw if w["s"] >= sg["srcIn"] - 1e-6 and w["e"] <= sg["srcOut"] + 1e-6]
                sg["words"] = [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in ws]
                sg["text"] = " ".join(w["w"] for w in ws).strip()
    for sg in segs:
        sg["id"] = "seg_" + uuid.uuid4().hex[:8]
        sg["mediaId"] = m["id"]
    return segs


def removed_ranges(m: dict[str, Any], segs: list[dict[str, Any]]) -> list[list[float]]:
    out, t = [], 0.0
    for s in sorted(segs, key=lambda x: x["srcIn"]):
        if s["srcIn"] - t > 0.05:
            out.append([round(t, 3), s["srcIn"]])
        t = max(t, s["srcOut"])
    end = IMAGE_SECONDS if m.get("isImage") else float(m["duration"])
    if end - t > 0.05:
        out.append([round(t, 3), round(end, 3)])
    return out


def rules_storyboard(project: dict[str, Any], segs_by_media: dict[str, list[dict[str, Any]]],
                     options: dict[str, Any]) -> dict[str, Any]:
    """AI bağlantısı olmadan: qaydalara əsaslanan storyboard (yaradıcı qərar vermir)."""
    cards = []
    order = [m["id"] for m in project["media"] if m["id"] in segs_by_media]
    for mid in order:
        for s in segs_by_media[mid]:
            cards.append({
                "id": "card_" + uuid.uuid4().hex[:8], "segmentId": s["id"], "mediaId": mid,
                "srcIn": s["srcIn"], "srcOut": s["srcOut"], "include": True,
                "role": "body", "transcript": s["text"], "words": s["words"],
                "onScreenText": "", "textStyle": "", "graphics": "", "broll": "", "transition": "kəsim",
                "reason": "Danışıq hissəsi; uzun pauzalarda bölünüb." if s["text"] else "Material hissəsi.",
                "source": "rules",
            })
    if cards:
        cards[0]["role"] = "opening"
    total = sum(c["srcOut"] - c["srcIn"] for c in cards)
    notes = []
    target = options.get("duration")
    if target and total > float(target) * 1.1:
        notes.append(f"Seçilmiş hissələr {total:.0f} san-dir, hədəf {float(target):.0f} san. "
                     "Qaydalara əsaslanan rejim məzmun seçmir — artıq hissələri özünüz söndürün və ya AI bağlantısını qoşun.")
    return {"generator": "rules", "cards": cards, "musicMood": "", "musicNote": "",
            "overallNote": " ".join(notes), "subtitles": "subtitle" in (options.get("extras") or [])}
