"""Arxa səsin təmizlənməsi (kafe uğultusu, uzaq danışıq, çəngəl-bıçaq, uzaqdan musiqi) — danışığı qoruyaraq.

* Model: DeepFilterNet3 (yerli, pulsuz, MIT/Apache-2.0). Orijinal səs dəyişmir — təmizlənmiş nüsxə
  `media/derived/<mid>.clean.wav` kimi yazılır və render yalnız danışıq qatında onu işlədir.
  Musiqi, SFX, B-roll / araya kadr səsi təmizlənmir.
* Danışığı qorumaq üçün: zəiflətmə həddi (standart 20 dB, tam silmə yox) + danışıq səviyyəsi orijinala bərabərləşdirilir.
* "auto": modelin çıxardığı enerji ölçülür; arxa səs azdırsa (studiya) təmizləmə TƏTBİQ EDİLMİR.
* Sınaq (süni kafe səsi, SNR 8 dB): pauzada arxa səs ~14 dB azaldı, danışıq keyfiyyəti (SI-SDR) 8.2 → 10.3 dB;
  təmiz danışığa təsir: SI-SDR 17 dB, səviyyə −0.7 dB (kompensasiya olunur). Yaxında danışan başqa adamın
  səsi də “danışıq”dır — tam silinmir; bunu istifadəçiyə demək lazımdır.
"""

from __future__ import annotations

import json
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np

SR = 48000
DEFAULT_ATTEN_DB = 20.0
NOISY_DB = -13.0   # çıxarılan enerji danışığa nisbətən bundan yüksəkdirsə — arxa səs var
MODEL_URL = "https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/models/DeepFilterNet3.zip"


def available() -> dict[str, Any]:
    import importlib.util

    ok = importlib.util.find_spec("df") is not None and importlib.util.find_spec("torch") is not None
    model = Path.home() / ".cache" / "DeepFilterNet" / "DeepFilterNet3" / "config.ini"
    return {"installed": ok, "model": model.is_file()}


def _shim_torchaudio() -> None:
    """DeepFilterNet 0.5.6 köhnə torchaudio.backend modulunu idxal edir (yalnız tip adı üçün)."""
    if "torchaudio.backend.common" in sys.modules:
        return
    try:
        import torchaudio.backend.common  # noqa: F401
        return
    except Exception:  # noqa: BLE001
        pass
    m = types.ModuleType("torchaudio.backend")
    mc = types.ModuleType("torchaudio.backend.common")

    class AudioMetaData:  # noqa: D401 - yalnız ad lazımdır
        pass

    mc.AudioMetaData = AudioMetaData
    m.common = mc
    sys.modules["torchaudio.backend"] = m
    sys.modules["torchaudio.backend.common"] = mc


_MODEL: tuple[Any, Any] | None = None


def _model():
    global _MODEL
    if _MODEL is None:
        _shim_torchaudio()
        from df.enhance import init_df

        model, state, _ = init_df()
        _MODEL = (model, state)
    return _MODEL


def _read(src: Path) -> np.ndarray:
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()


def enhance(audio: np.ndarray, atten_db: float | None = DEFAULT_ATTEN_DB) -> np.ndarray:
    import torch

    model, state = _model()  # əvvəl: torchaudio uyğunluq düzəlişi + model
    from df.enhance import enhance as df_enhance

    y = df_enhance(model, state, torch.from_numpy(audio)[None], atten_lim_db=atten_db)[0].numpy()
    return y[: len(audio)] if len(y) >= len(audio) else np.pad(y, (0, len(audio) - len(y)))


def _speech_rms(x: np.ndarray, ref: np.ndarray) -> float:
    fr = SR // 100
    k = len(ref) // fr
    e = np.sqrt((ref[: k * fr].reshape(k, fr) ** 2).mean(1))
    sel = e > np.percentile(e, 55)  # danışıq çərçivələri (təmizlənmiş səsə görə)
    xx = x[: k * fr].reshape(k, fr)
    return float(np.sqrt((xx[sel] ** 2).mean())) if sel.any() else float(np.sqrt((x ** 2).mean()))


def clean_media(project_dir: Path, m: dict[str, Any], mode: str = "auto", atten_db: float = DEFAULT_ATTEN_DB) -> dict[str, Any]:
    """Bir media üçün təmizlənmiş danışıq faylı. Nəticə: {applied, removedDb, file?, gainDb, why}."""
    src = project_dir / m["file"]
    dst_rel = f"media/derived/{m['id']}.clean.wav"
    dst = project_dir / dst_rel
    meta = dst.with_suffix(".json")
    key = {"size": src.stat().st_size, "atten": atten_db, "model": "DeepFilterNet3", "v": 2}
    if dst.is_file() and meta.is_file():
        old = json.loads(meta.read_text())
        if old.get("key") == key:
            res = old["result"]
            if mode == "on" or (mode == "auto" and res["removedDb"] > NOISY_DB):
                return {**res, "applied": True, "file": dst_rel}
            return {**res, "applied": False, "why": res.get("why") or "arxa səs az"}
    x = _read(src)
    y = enhance(x, atten_db)
    removed = float(np.sqrt(((x - y) ** 2).mean()))
    sp = _speech_rms(x, y)
    removed_db = round(20 * np.log10(max(removed, 1e-7) / max(sp, 1e-7)), 1)
    gain = _speech_rms(x, y) / max(_speech_rms(y, y), 1e-7)  # danışıq səviyyəsi orijinala bərabər
    gain = float(np.clip(gain, 0.7, 1.6))
    y = np.clip(y * gain, -0.99, 0.99).astype(np.float32)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # stereo kimi yazılır (hər iki kanal eyni): mono→stereo çevrilməsində ffmpeg-in −3 dB azaltmasının qarşısı
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "pan=stereo|c0=c0|c1=c0", "-c:a", "pcm_s16le", str(dst)],
                   input=y.tobytes(), check=True)
    res = {"removedDb": removed_db, "gainDb": round(20 * np.log10(gain), 1), "atten": atten_db}
    meta.write_text(json.dumps({"key": key, "result": res}))
    if mode == "on" or (mode == "auto" and removed_db > NOISY_DB):
        return {**res, "applied": True, "file": dst_rel}
    return {**res, "applied": False, "why": f"arxa səs az ({removed_db} dB) — təmizləmə lazım deyil"}


def ab_sample(project_dir: Path, m: dict[str, Any], clean_rel: str, out: Path, start: float, seconds: float = 6) -> Path:
    """Əvvəl / sonra dinləmə nümunəsi: orijinal, qısa sükut, təmizlənmiş (eyni hissə)."""
    a, b = project_dir / m["file"], project_dir / clean_rel
    fc = (f"[0:a]atrim={start}:{start + seconds},asetpts=N/SR/TB,aresample={SR},aformat=channel_layouts=mono[o];"
          f"[1:a]atrim={start}:{start + seconds},asetpts=N/SR/TB,aresample={SR},aformat=channel_layouts=mono[c];"
          f"aevalsrc=0:s={SR}:d=0.8[s];[o][s][c]concat=n=3:v=0:a=1[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-i", str(b), "-filter_complex", fc, "-map", "[out]",
                    "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    return out
