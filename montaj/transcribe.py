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

DEFAULT_MODEL = os.environ.get("MONTAJ_WHISPER_MODEL", "small")

# Azərbaycan dilində tipik pauza/doldurucu sözlər (kiçik hərflə, durğu işarəsiz).
AZ_FILLERS = {"ee", "eee", "eeee", "ə", "əə", "əəə", "ıı", "ııı", "hmm", "hm", "mm", "mmm", "ah", "eh", "ım", "ıı"}


def available() -> dict[str, Any]:
    installed = importlib.util.find_spec("faster_whisper") is not None
    return {"installed": installed, "model": DEFAULT_MODEL}


def transcribe(src: Path, start: float, end: float, language: str | None = "az") -> dict[str, Any]:
    from faster_whisper import WhisperModel  # yalnız lazım olanda yüklənir

    from montaj.media import read_mono

    model = WhisperModel(DEFAULT_MODEL, device="cpu", compute_type="int8")
    # PyAV versiya fərqlərindən asılı olmamaq üçün səsi ffmpeg ilə oxuyuruq
    audio = read_mono(src, 16000)
    a, b = int(max(0, start) * 16000), int(end * 16000)
    segments, info = model.transcribe(
        audio[a:b], language=language or None, word_timestamps=True, vad_filter=False,
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


def norm_word(w: str) -> str:
    return "".join(ch for ch in w.lower() if ch.isalpha())


def filler_ranges(words: list[dict[str, Any]]) -> list[tuple[float, float]]:
    out = []
    for w in words:
        if norm_word(w["w"]) in AZ_FILLERS:
            out.append((w["s"], w["e"]))
    return out
