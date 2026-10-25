"""Meta MMS local text-to-speech provider tool (VITS via sherpa-onnx, 1000+ languages incl. Azerbaijani)."""

from __future__ import annotations

import re
import time
import urllib.request
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

DEFAULT_LANGUAGE = "azj-script_latin"
MODEL_REPO = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main"
CACHE_DIR = Path.home() / ".cache" / "openmontage" / "mms-tts"

_DIGITS_AZ = {
    "0": "sıfır", "1": "bir", "2": "iki", "3": "üç", "4": "dörd",
    "5": "beş", "6": "altı", "7": "yeddi", "8": "səkkiz", "9": "doqquz",
}


class MmsTTS(BaseTool):
    name = "mms_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "meta_mms"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["python:sherpa_onnx"]
    install_instructions = (
        "Install the ONNX runtime for Meta MMS-TTS:\n"
        "  pip install sherpa-onnx onnxruntime\n"
        "The voice model (~110 MB per language) downloads from Hugging Face on first use\n"
        "(default: azj-script_latin — Azerbaijani; MMS weights are CC-BY-NC-4.0)."
    )
    agent_skills = ["mms-tts"]

    capabilities = [
        "text_to_speech",
        "offline_generation",
        "low_resource_languages",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
    }
    best_for = [
        "free narration in languages without Piper/commercial voices (Azerbaijani, etc.)",
        "zero-cost local fallback for low-resource languages",
    ]
    not_good_for = [
        "expressive or emotional delivery",
        "commercial projects (MMS weights are CC-BY-NC-4.0)",
        "broadcast audio quality (16 kHz output)",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "language": {
                "type": "string",
                "default": DEFAULT_LANGUAGE,
                "description": "MMS language code, e.g. azj-script_latin, tur, kaz, rus",
            },
            "speed": {
                "type": "number",
                "default": 1.0,
                "description": ">1 faster, <1 slower",
            },
            "noise_scale": {
                "type": "number",
                "default": 0.667,
                "description": "Prosody variation; lower = flatter, higher = livelier",
            },
            "sentence_silence": {
                "type": "number",
                "default": 0.35,
                "description": "Seconds of silence inserted between sentences",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=600, vram_mb=0, disk_mb=150, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=[])
    idempotency_key_fields = ["text", "language", "speed", "noise_scale"]
    side_effects = ["writes audio file to output_path", "caches model under ~/.cache/openmontage/mms-tts"]
    user_visible_verification = ["Listen to generated audio for intelligibility and stress"]

    _cache: dict[tuple, Any] = {}

    def get_status(self) -> ToolStatus:
        try:
            import sherpa_onnx  # noqa: F401
        except ImportError:
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(success=False, error="MMS-TTS not available. " + self.install_instructions)

        start = time.time()
        try:
            result = self._generate(inputs)
        except Exception as exc:
            return ToolResult(success=False, error=f"MMS-TTS generation failed: {exc}")

        result.duration_seconds = round(time.time() - start, 2)
        return result

    @staticmethod
    def normalize_text(text: str) -> str:
        """MMS vocab has lowercase letters only (no punctuation): spell digits, drop the rest."""
        text = re.sub(r"\[[^\]]*\]", " ", text)  # drop ElevenLabs-style audio tags
        text = re.sub(r"\d", lambda m: " " + _DIGITS_AZ[m.group(0)] + " ", text)
        text = text.replace("İ", "i").replace("I", "ı").lower()
        text = re.sub(r"[^\w\s'-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def split_sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?…])\s+|\s+[—–]\s+", text.strip())
        return [p for p in parts if p.strip()]

    def _model_dir(self, language: str) -> Path:
        d = CACHE_DIR / language
        for fname in ("model.onnx", "tokens.txt"):
            if not (d / fname).exists():
                d.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(f"{MODEL_REPO}/{language}/{fname}", d / fname)
        return d

    def _load(self, language: str, noise_scale: float):
        key = (language, noise_scale)
        if key not in self._cache:
            import sherpa_onnx

            d = self._model_dir(language)
            vits = sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(d / "model.onnx"), tokens=str(d / "tokens.txt"), noise_scale=noise_scale
            )
            cfg = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(vits=vits, num_threads=4)
            )
            self._cache[key] = sherpa_onnx.OfflineTts(cfg)
        return self._cache[key]

    def _generate(self, inputs: dict[str, Any]) -> ToolResult:
        import numpy as np
        import scipy.io.wavfile

        language = inputs.get("language", DEFAULT_LANGUAGE)
        output_path = Path(inputs.get("output_path", "tts_output.wav"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        tts = self._load(language, float(inputs.get("noise_scale", 0.667)))
        speed = float(inputs.get("speed", 1.0))

        chunks: list[np.ndarray] = []
        rate = 16000
        sentences = self.split_sentences(inputs["text"])
        for sentence in sentences:
            norm = self.normalize_text(sentence)
            if not norm:
                continue
            audio = tts.generate(norm, sid=0, speed=speed)
            rate = audio.sample_rate
            gap = np.zeros(int(rate * float(inputs.get("sentence_silence", 0.35))), dtype=np.float32)
            chunks.extend([np.asarray(audio.samples, dtype=np.float32), gap])

        if not chunks:
            return ToolResult(success=False, error="No speakable text after normalization")

        audio = np.concatenate(chunks[:-1])
        peak = float(np.max(np.abs(audio))) or 1.0
        pcm = (audio / peak * 0.9 * 32767).astype(np.int16)
        scipy.io.wavfile.write(str(output_path), rate, pcm)

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "language": language,
                "sentences": len(sentences),
                "audio_seconds": round(len(pcm) / rate, 2),
                "sample_rate": rate,
                "output": str(output_path),
                "format": "wav",
            },
            artifacts=[str(output_path)],
            model=f"mms-tts-{language}",
            cost_usd=0.0,
        )
