#!/usr/bin/env python3
"""Transcribe a wav with faster-whisper large-v3 (Azerbaijani) into the transcriber tool's
JSON shape ({"segments": [...], "word_timestamps": [...]}) - a fallback when the
registry tool fails on a file.

Usage: transcribe.py <in.wav> <out.json> [language=az]
"""
import json
import sys

from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
lang = sys.argv[3] if len(sys.argv) > 3 else "az"
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs, _ = m.transcribe(src, language=lang, word_timestamps=True, vad_filter=False, condition_on_previous_text=False)
S, W = [], []
for s in segs:
    S.append({"start": s.start, "end": s.end, "text": s.text.strip()})
    W += [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for w in s.words]
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
json.dump({"segments": S, "word_timestamps": W}, open(out, "w"), ensure_ascii=False)
