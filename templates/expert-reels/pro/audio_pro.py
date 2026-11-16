"""Peşəkar danışıq səsi zənciri — təbii tembr qorunur, «boğuq/metalik» olmasın.

Niyə: köhnə zəncir hər videoya eyni güclü küy təmizləmə (DeepFilterNet 20–30 dB) + fasilələrdə səsi
söndürmə tətbiq edirdi → bəzən səs boğuq/metalik çıxırdı. Bu modul əvvəl küyü ÖLÇÜR, gücü ona görə seçir,
sonra studiya ardıcıllığı ilə emal edir və nəticəni ölçərək müqayisə edir.

Ardıcıllıq: [Demucs vokal ayırma — yalnız musiqi/kənar səs varsa] → DeepFilterNet (ölçülmüş güc)
→ HPF 75 Hz → palçıq kəsimi 250 Hz → mövcudluq 3.5 kHz → hava 10 kHz → kompressor → de-esser
→ LUFS normallaşdırma (iki keçidli, kəsilmə yox) → limiter (−1.5 dBTP).

İstifadə:
  python3 audio_pro.py <giriş(video/wav)> <çıxış.wav> [--isolate] [--target -14] [--report r.json]
  python3 audio_pro.py --measure <fayl>          # yalnız ölçü (QA üçün)
"""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

SR = 48000


def load(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def save(path, x, sr=SR):
    import soundfile as sf
    sf.write(str(path), np.clip(x, -1, 1), sr, subtype="PCM_24")


def measure(x, sr=SR):
    import pyloudnorm as pyln
    lufs = float(pyln.Meter(sr).integrated_loudness(x.astype(np.float64))) if len(x) > sr else -70.0
    hop = int(sr * 0.05); fr = x[: len(x) // hop * hop].reshape(-1, hop); rms = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    floor = float(np.percentile(rms, 3)); speech = float(np.percentile(rms, 90))  # 3%: həqiqi pauzalar (10% danışıq quyruğunu tuturdu)
    X = np.abs(np.fft.rfft(x[: min(len(x), sr * 60)] * np.hanning(min(len(x), sr * 60)))) ** 2; f = np.fft.rfftfreq(min(len(x), sr * 60), 1 / sr)
    band = lambda a, b: X[(f >= a) & (f < b)].sum()
    hf = float(band(3000, 8000) / max(1e-12, band(100, 8000)))      # «boğuqluq» göstəricisi: azdırsa səs boğuqdur
    mud = float(band(150, 400) / max(1e-12, band(100, 8000)))
    return {"lufs": round(lufs, 1), "noise_floor_db": round(floor, 1), "speech_db": round(speech, 1), "snr_db": round(speech - floor, 1),
            "hf_ratio": round(hf, 4), "mud_ratio": round(mud, 3), "peak_db": round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1)}


def denoise_strength(m):
    """Küy səviyyəsinə görə DeepFilterNet gücü (dB). Təmiz səsə toxunulmur — boğuqluğun əsas səbəbi."""
    snr = m["snr_db"]
    if snr >= 45: return 0
    if snr >= 38: return 8
    if snr >= 30: return 12
    return 18


def dfn(x, atten):
    if atten <= 0: return x
    d = Path(tempfile.mkdtemp()); a, b = d / "a.wav", d / "b.wav"
    import soundfile as sf
    sf.write(str(a), x, SR, subtype="PCM_16")
    here = Path(__file__).resolve().parent
    tool = here / "dfn.py" if (here / "dfn.py").exists() else Path(__file__).resolve().parents[3] / "instagram-clients/_agency/stil_Ulker/aletler/dfn.py"
    r = subprocess.run([sys.executable, str(tool), str(a), str(b), str(atten)], capture_output=True, text=True)
    if r.returncode or not b.exists():
        print("DeepFilterNet işləmədi, keçilir:", r.stderr[-200:]); return x
    return load(b)


def isolate(path):
    """Demucs htdemucs: vokalı musiqi/kənar səslərdən ayırır (CPU-da yavaşdır — yalnız lazım olanda)."""
    d = Path(tempfile.mkdtemp()); w = d / "in.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "2", "-ar", "44100", str(w)], check=True)
    subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(d), str(w)], check=True, capture_output=True)
    return load(next(d.rglob("vocals.wav")))


def chain(x, m):
    from pedalboard import Pedalboard, HighpassFilter, PeakFilter, HighShelfFilter, Compressor, NoiseGate
    boost = 2.5 if m["hf_ratio"] < 0.04 else (1.5 if m["hf_ratio"] < 0.08 else 0.5)   # boğuqdursa daha çox «presence»
    mudcut = -4.0 if m["mud_ratio"] > 0.45 else (-2.5 if m["mud_ratio"] > 0.35 else -1.5)
    # yumşaq ekspander (qapı deyil): pauzalarda otaq küyü kompressor tərəfindən qaldırılmasın; nəfəs təbii qalır
    gate = NoiseGate(threshold_db=m["noise_floor_db"] + 9, ratio=1.8, attack_ms=3, release_ms=220)
    pb = Pedalboard([HighpassFilter(75), gate, PeakFilter(250, mudcut, 1.0), PeakFilter(3500, boost, 0.9), HighShelfFilter(10000, 1.0, 0.7),
                     Compressor(threshold_db=m["speech_db"] - 8, ratio=2.2, attack_ms=10, release_ms=150)])
    y = pb(x.reshape(1, -1).astype(np.float32), SR)[0]
    # de-esser (ffmpeg): yalnız sərt «s/ş» səsləri yumşaldılır
    d = Path(tempfile.mkdtemp()); a, b = d / "a.wav", d / "b.wav"; save(a, y)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-af", "deesser=i=0.35:m=0.5:f=0.5", str(b)], check=True)
    return load(b)


def finish(y, target):
    """Qazanc → sürətli pik kompressoru → yumşaq doyma (tanh) → kiçik LUFS düzəlişi. Sərt limiter klik yaradırdı (ölçülüb)."""
    import pyloudnorm as pyln
    from pedalboard import Pedalboard, Compressor
    M = pyln.Meter(SR); y = y.astype(np.float32)
    for _ in range(2):
        lufs = M.integrated_loudness(y.astype(np.float64)); y = (y * (10 ** ((target - lufs) / 20))).astype(np.float32)
        y = Pedalboard([Compressor(threshold_db=-9, ratio=5, attack_ms=1.5, release_ms=90)])(y.reshape(1, -1), SR)[0]
        ceil = 0.84; y = (np.tanh(y / ceil) * ceil).astype(np.float32)   # −1.5 dBFS tavan, yumşaq
    lufs = M.integrated_loudness(y.astype(np.float64)); g = 10 ** ((target - lufs) / 20)   # son kiçik düzəliş
    y = (np.tanh(y * g / 0.84) * 0.84).astype(np.float32)
    # gücləndirmədən sonra «p/b» partlayışları çıqqıltıya çevrilə bilir — adeclick təmizləyir (QC ilə ölçülüb: 5 → 0)
    d = Path(tempfile.mkdtemp()); a, b = d / "a.wav", d / "b.wav"; save(a, y)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-af", "adeclick=w=55:o=75", str(b)], check=True)
    z = load(b); return z[: len(y)] if len(z) >= len(y) else np.pad(z, (0, len(y) - len(z)))


def gentle(x, m, target):
    """Yumşaq rejim (təmiz yazı üçün): tembr dəyişmir — yalnız HPF, palçıq üçün kiçik kəsim, tək yüngül kompressor,
    LUFS qazancı və yumşaq tavan. Qapı/ekspander, «presence» qaldırma, ikiqat kompressor yoxdur
    (16.11.2026: güclü zəncir təmiz kafe yazısında səsi metallik/«təkrarlı» etdi — otaq əks-sədası önə çıxdı)."""
    import pyloudnorm as pyln
    from pedalboard import Pedalboard, HighpassFilter, PeakFilter, Compressor
    y = Pedalboard([HighpassFilter(80), PeakFilter(250, -1.5, 1.0), Compressor(threshold_db=m["speech_db"] - 6, ratio=1.8, attack_ms=15, release_ms=200)])(
        x.reshape(1, -1).astype(np.float32), SR)[0]
    M = pyln.Meter(SR); lufs = M.integrated_loudness(y.astype(np.float64))
    y = y * (10 ** ((target - lufs) / 20)); return (np.tanh(y / 0.89) * 0.89).astype(np.float32)


def process(src, dst, do_isolate=False, target=-14.0, mode="auto"):
    """mode: auto (ölçülmüş tam zəncir) | gentle (təmiz yazı: ≤6 dB küy təmizləmə + gentle())."""
    x = isolate(src) if do_isolate else load(src)
    m0 = measure(x); att = denoise_strength(m0)
    if mode == "gentle":
        att = min(att, 6); y = gentle(dfn(x, att), m0, target)
    else:
        y = finish(chain(dfn(x, att), m0), target)
    save(dst, y)
    m1 = measure(y)
    return {"before": m0, "after": m1, "denoise_db": att, "isolate": do_isolate, "mode": mode}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst", nargs="?"); ap.add_argument("--isolate", action="store_true")
    ap.add_argument("--target", type=float, default=-14.0); ap.add_argument("--report"); ap.add_argument("--measure", action="store_true")
    a = ap.parse_args()
    if a.measure: print(json.dumps(measure(load(a.src)), ensure_ascii=False)); return
    r = process(a.src, a.dst, a.isolate, a.target)
    if a.report: json.dump(r, open(a.report, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
