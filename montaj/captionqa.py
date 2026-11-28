"""Altyazı sözlərinin yekun SƏSə görə yoxlanması.

Altyazı mətni transkriptdən qurulur və əl ilə düzəldilə bilər (lüğət, `fix-word`, plan `corrections`). Burada hazır videonun səsi
iki fərqli tanıma ilə (turbo və tam large-v3) yenidən oxunur və hər altyazı sözü eşidilənlə tutuşdurulur. Hər iki tanımanın eşitdiyinə
(hərf qarışıqlıqları ə/e, ğ/x/q... nəzərə alınmaqla) uyğun gəlməyən söz "yoxlayın" siyahısına düşür — istifadəçiyə təhvildə göstərilir.
Qulaq əvəzi deyil: ASR özü səhv edə bilər; amma "mən yazdım, ASR başqa eşitdi" yerləri avtomatik tapılır.

İstifadə: python -m montaj.captionqa <pid> <yekun.mp4> [--models large-v3-turbo,large-v3]
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Any

import numpy as np

from montaj.transcribe import fold

TOL = 1.8          # altyazı sözünün vaxtı ilə ASR sözünün vaxtı arası icazə (s)
MATCH = 0.78       # hərf-qarışıqlığı nəzərə alınmış oxşarlıq həddi


def _words(audio: np.ndarray, model_name: str, hotwords: str | None) -> list[tuple[str, float, float]]:
    from faster_whisper import WhisperModel

    m = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="az", word_timestamps=True, beam_size=5, condition_on_previous_text=False, hotwords=hotwords or None)
    return [(fold(w.word), float(w.start), float(w.end)) for s in segs for w in (s.words or []) if fold(w.word)]


def compare(cues: list[tuple[float, float, str]], heard: dict[str, list[tuple[str, float, float]]]) -> list[dict[str, Any]]:
    """cues: [(başla, bitir, mətn)] (zaman xətti); heard: {model: [(qatlanmış_söz, s, e)]}. Qayıdır eşidilənə uyğun gəlməyən altyazı sözləri."""
    out: list[dict[str, Any]] = []
    for a, b, text in cues:
        toks = text.split()
        if not toks:
            continue
        for i, tok in enumerate(toks):
            f = fold(tok)
            if len(f) < 3:
                continue
            t = a + (b - a) * (i + 0.5) / len(toks)  # söz vaxtı təxmini (altyazı daxilində bərabər)
            seen: dict[str, str] = {}
            ok = False
            for name, ws in heard.items():
                near = [w for w in ws if w[2] >= t - TOL and w[1] <= t + TOL]
                best = max(near, key=lambda w: difflib.SequenceMatcher(None, f, w[0]).ratio(), default=None)
                r = difflib.SequenceMatcher(None, f, best[0]).ratio() if best else 0.0
                seen[name] = best[0] if best else "—"
                ok = ok or r >= MATCH
            if not ok:
                out.append({"t": round(t, 2), "caption": tok, "heard": seen})
    return out


def run(pid: str, video: Path, models: list[str]) -> list[dict[str, Any]]:
    from montaj import session as s, store
    from montaj.media import read_mono
    from montaj.session import expert_profile, glossary_terms

    p = store.load(pid)
    cues = s.captions_cues(p)
    br = p.get("brand") or {}
    prof = expert_profile(br["name"]) if br.get("name") else None
    hot = " ".join(glossary_terms(prof)) if prof else None
    audio = read_mono(video, 16000)
    heard = {m: _words(audio, m, hot) for m in models}
    return compare(cues, heard)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pid")
    ap.add_argument("video")
    ap.add_argument("--models", default="large-v3-turbo,large-v3")
    a = ap.parse_args(argv)
    bad = run(a.pid, Path(a.video), [m for m in a.models.split(",") if m])
    if not bad:
        print("altyazı yoxlaması: bütün sözlər eşidilənə uyğundur (qulaqla yoxlanmayıb)")
        return 0
    print(f"altyazı yoxlaması: {len(bad)} söz yoxlanmalıdır (hər iki tanıma başqa eşitdi — özünüz dinləyib təsdiq edin):")
    for x in bad:
        heard = ", ".join(f"{k}: «{v}»" for k, v in x["heard"].items())
        print(f"  {x['t']:.1f} s  altyazı «{x['caption']}»  ←  {heard}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
