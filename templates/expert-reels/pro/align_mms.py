"""Düzgün mətni səsə dəqiq oturtmaq (forced alignment) — Meta MMS (1100+ dil, Azərbaycan daxil), torchaudio.

Niyə: Whisper söz vaxtları ±0.1–0.3 s səhv ola bilir; sözün sonu tez bitmiş görünəndə kəsim heca yeyirdi,
altyazı da sinxron getmirdi. MMS_FA düzgün (redaktə olunmuş) mətnin hər sözünü səs dalğasına oturdur.

İstifadə (modul):  align(wav_path, text, start=0.0, end=None) → [(s, e, söz, bal), ...]
CLI: python3 align_mms.py <video|wav> "<mətn>" [--start S --end E]
Qeyd: model ~1.2 GB, ilk dəfə endirilir (torchaudio hub). CPU-da 1 dəqiqə səs ≈ bir neçə saniyə.
"""
import json, subprocess, sys, unicodedata
import numpy as np

ROM = str.maketrans({"ə": "e", "ı": "i", "ö": "o", "ü": "u", "ş": "s", "ç": "c", "ğ": "g", "x": "x", "q": "q", "İ": "i", "Ə": "e", "I": "i",
                     "Ö": "o", "Ü": "u", "Ş": "s", "Ç": "c", "Ğ": "g"})
_M = {}


def _model():
    if not _M:
        import torch
        from torchaudio.pipelines import MMS_FA as B
        _M.update(model=B.get_model().eval(), dict=B.get_dict(), sr=B.sample_rate, torch=torch)
    return _M


def romanize(w):
    w = w.translate(ROM).lower()
    w = unicodedata.normalize("NFKD", w)
    return "".join(c for c in w if c in _model()["dict"] and c != "-")


def load(path, sr, start=0.0, end=None):
    a = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"] + (["-to", f"{end:.3f}"] if end else []) + ["-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(a, capture_output=True).stdout, np.float32).copy()


def align(path, text, start=0.0, end=None):
    M = _model(); torch = M["torch"]; words = text.split(); toks = [romanize(w) for w in words]
    keep = [i for i, t in enumerate(toks) if t]
    if not keep: return []
    x = torch.from_numpy(load(path, M["sr"], start, end))[None]
    with torch.inference_mode():
        em, _ = M["model"](x)
    import torchaudio.functional as F
    tgt = torch.tensor([[M["dict"][c] for i in keep for c in toks[i]]], dtype=torch.int32)
    ali, sc = F.forced_align(em, tgt, blank=0)
    spans = F.merge_tokens(ali[0], sc[0].exp())
    ratio = x.shape[1] / em.shape[1] / M["sr"]
    out, k = [], 0
    for i in keep:
        n = len(toks[i]); sp = spans[k:k + n]; k += n
        s = start + sp[0].start * ratio; e = start + sp[-1].end * ratio
        out.append((round(s, 3), round(e, 3), words[i], round(float(np.mean([t.score for t in sp])), 3)))
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("text"); ap.add_argument("--start", type=float, default=0); ap.add_argument("--end", type=float)
    a = ap.parse_args(); print(json.dumps(align(a.src, a.text, a.start, a.end), ensure_ascii=False))
