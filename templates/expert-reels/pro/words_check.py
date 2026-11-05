"""Altyazı yoxlaması (render-dən ƏVVƏL): ASR-in əmin olmadığı sözləri işarələyir.

  python3 words_check.py <video.json> [hədd=0.6]
Nəticə: <PRO_WORK>/vN_yoxla.md — hər şübhəli söz vaxtı və konteksti ilə.
Düzəlişlər konfiqə yazılır:  "corrections": [{"from": "səhv", "to": "düz"}]
(müştəriyə aid daimi düzəlişlər brend kitində "glossary"-yə). Sonra build.py.
"""
import glob, json, subprocess, sys
import numpy as np
import kit

CFG, B, _ = kit.load(sys.argv[1]); TH = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
pid = CFG.get("pid"); src = glob.glob(str(kit.DATA / "projects" / pid / "media" / "originals" / "*"))[0]
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768  # PCM birbaşa (PyAV versiya xətasından yan keçir)
from faster_whisper import WhisperModel
m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")
segs, _ = m.transcribe(a, language=CFG.get("lang", "az"), word_timestamps=True, vad_filter=False, condition_on_previous_text=False,
                       initial_prompt=" ".join(t["to"] for t in B.get("glossary", [])) or None)
W = [w for s in segs for w in s.words]
known = {t["to"].lower() for t in B.get("glossary", []) + CFG.get("corrections", [])}
flag = [(i, w) for i, w in enumerate(W) if w.probability < TH and w.word.strip().lower() not in known and len(w.word.strip()) > 1]
out = kit.WORK / f"v{CFG['n']}_yoxla.md"
L = [f"# Altyazı yoxlaması — v{CFG['n']} ({len(flag)} şübhəli söz, hədd {TH})", "",
     "| vaxt | söz | əminlik | kontekst |", "|---|---|---|---|"]
for i, w in flag:
    ctx = " ".join(x.word.strip() for x in W[max(0, i - 4):i]) + f" **{w.word.strip()}** " + " ".join(x.word.strip() for x in W[i + 1:i + 5])
    L.append(f"| {w.start:6.2f} | {w.word.strip()} | {w.probability:.2f} | {ctx} |")
L += ["", "Düzəliş: konfiqə `\"corrections\": [{\"from\": \"…\", \"to\": \"…\"}]` yaz və ya brend kitinin `glossary` siyahısına əlavə et."]
out.write_text("\n".join(L), encoding="utf-8"); print(f"şübhəli söz: {len(flag)} → {out}")
