"""Yerli transkripsiya (faster-whisper) və söz əsaslı təkliflər.

API açarı tələb etmir. Model ilk dəfə Hugging Face-dən endirilir
(huggingface.co şəbəkə icazəsi lazımdır), sonra keşdən işləyir.
Azərbaycan dilində söz sərhədlərinin keyfiyyəti real Azərbaycan dilli
video ilə yoxlanılmayıb — UI bunu açıq göstərir.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

# large-v3-turbo: Azərbaycan dilində "small"-dan xeyli dəqiqdir (Günel videosunda sınaqdan keçib), CPU-da ~0.5x real vaxt
DEFAULT_MODEL = os.environ.get("MONTAJ_WHISPER_MODEL", "large-v3-turbo")

# Azərbaycan dilində tipik pauza/doldurucu sözlər (kiçik hərflə, durğu işarəsiz).
AZ_FILLERS = {"ee", "eee", "eeee", "ə", "əə", "əəə", "ıı", "ııı", "hmm", "hm", "mm", "mmm", "ah", "eh", "ım", "ıı"}


def available() -> dict[str, Any]:
    installed = importlib.util.find_spec("faster_whisper") is not None
    return {"installed": installed, "model": DEFAULT_MODEL}


def transcribe(src: Path, start: float, end: float, language: str | None = "az", hotwords: str | None = None) -> dict[str, Any]:
    from faster_whisper import WhisperModel  # yalnız lazım olanda yüklənir

    from montaj.media import read_mono

    model = WhisperModel(DEFAULT_MODEL, device="cpu", compute_type="int8")
    # PyAV versiya fərqlərindən asılı olmamaq üçün səsi ffmpeg ilə oxuyuruq
    audio = read_mono(src, 16000)
    a, b = int(max(0, start) * 16000), int(end * 16000)
    # Sınaq (Rəhimə, 4 video): condition_on_previous_text=False + beam 5 + müştəri lüğəti (hotwords) söz xətasını ~0.47 → ~0.10-a endirdi.
    # Uzun kontekstə bağlı tanıma (standart) əvvəlki səhv sözü təkrar edir ("baxçıb əlum"), danışıqsız yerdə uydurur.
    segments, info = model.transcribe(
        audio[a:b], language=language or None, word_timestamps=True, beam_size=5, condition_on_previous_text=False,
        vad_filter=True, vad_parameters={"threshold": 0.35, "min_silence_duration_ms": 600, "speech_pad_ms": 200},
        hotwords=hotwords or None,  # müştərinin terminləri/adları (lüğətdən) — düzgün tanınma ehtimalı artır
    )
    words: list[dict[str, Any]] = []
    text_parts: list[str] = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        for w in seg.words or []:
            words.append({
                "w": w.word.strip(),
                "s": round(float(start + w.start), 3),
                "e": round(float(start + w.end), 3),
                "p": round(float(w.probability), 3),
            })
    return {
        "language": info.language,
        "languageProbability": round(float(info.language_probability), 3),
        "model": DEFAULT_MODEL,
        "text": " ".join(text_parts),
        "words": words,
    }


_FOLD = str.maketrans({"ə": "e", "ı": "i", "İ": "i", "ö": "o", "ü": "u", "ş": "s", "ç": "c", "ğ": "g", "x": "g", "q": "g", "w": "v"})


def fold(w: str) -> str:
    """Azərbaycan hərflərini ASR-in qarışdırdığı qruplara endirir (ə→e, ğ/x/q→g, ş→s ...): "baxça" ≡ "bağça", "məşqalə" ≡ "məşğələ"."""
    return "".join(ch for ch in w.lower().replace("i̇", "i") if ch.isalpha()).translate(_FOLD)


def snap_glossary(words: list[dict[str, Any]], terms: list[str], min_ratio: float = 1.0) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    """Müştəri lüğətindəki sözlərə yaxın ASR sözlərini düzgün yazılışa çevirir (yalnız bütöv söz, ayrı-ayrılıqda).
    Tam eyni yazılış toxunulmur. Qayıdır (yeni sözlər, [(köhnə, yeni)]). Böyük hərf/durğu qorunur."""
    import difflib

    index: dict[str, str] = {}
    for t in terms:
        for tok in str(t).split():
            if len(fold(tok)) >= 4:
                index.setdefault(fold(tok), tok)
    out, changed = [], []
    for w in words:
        raw = w["w"]
        core = raw.strip(".,!?;:\"'«»()—-")
        lead = raw[: len(raw) - len(raw.lstrip(".,!?;:\"'«»()—-"))]
        tail = raw[len(lead) + len(core):]
        f = fold(core)
        new = None
        if len(f) >= 4 and core not in terms:
            if f in index and index[f] != core:
                new = index[f]
            else:
                best = difflib.get_close_matches(f, list(index), n=1, cutoff=min_ratio)
                if best and index[best[0]] != core:
                    new = index[best[0]]
        if new:
            if core[:1].isupper() and not new[:1].isupper():
                new = new[:1].upper() + new[1:]
            changed.append((raw, lead + new + tail))
            out.append({**w, "w": lead + new + tail})
        else:
            out.append(w)
    return out, changed


def uncertain(words: list[dict[str, Any]], below: float = 0.55) -> list[dict[str, Any]]:
    """Əminlik ehtimalı aşağı olan sözlər — təhvildə istifadəçiyə "bu sözlər düzgündürmü" siyahısı kimi göstərilir."""
    return [w for w in words if w.get("p") is not None and float(w["p"]) < below]


def norm_word(w: str) -> str:
    return "".join(ch for ch in w.lower() if ch.isalpha())


def filler_ranges(words: list[dict[str, Any]]) -> list[tuple[float, float]]:
    out = []
    for w in words:
        if norm_word(w["w"]) in AZ_FILLERS:
            out.append((w["s"], w["e"]))
    return out
