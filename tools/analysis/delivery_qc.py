"""Delivery QC — objective, broadcast-style quality control for a finished render.

A human finishing editor runs a QC pass before anything ships. This tool does
the measurable half of that pass in two FFmpeg decodes:

- Spec: resolution, frame rate, pixel format (yuv420p), codecs, audio present
- Loudness: integrated LUFS, loudness range, true peak (EBU R128) vs platform target
- Black frames and frozen frames (stuck renders, dead slideshow holds)
- Dead air: silences inside the programme
- Rhythm: cut count, cuts per minute, average and longest shot length vs format norms

The subjective half (story, taste, typography) lives in skills/meta/editor-qc.md.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolTier,
)

# Integrated loudness target (LUFS), tolerance, max true peak (dBTP)
LOUDNESS_TARGETS = {
    "social": (-14.0, 1.5, -1.0),      # TikTok / Reels / Shorts
    "youtube": (-14.0, 1.5, -1.0),
    "podcast": (-16.0, 1.5, -1.0),
    "broadcast": (-23.0, 1.0, -2.0),   # EBU R128
    "cinema_web": (-18.0, 2.0, -1.0),  # dynamic long-form / film-style
}

# Shot-length norms in seconds: (max average shot length, max single static shot)
RHYTHM_NORMS = {
    "short_form": (3.5, 6.0),
    "ad": (2.5, 5.0),
    "explainer": (5.0, 9.0),
    "talking_head": (8.0, 20.0),
    "documentary": (8.0, 25.0),
    "cinematic": (6.0, 15.0),
}


class DeliveryQC(BaseTool):
    name = "delivery_qc"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "analysis"
    provider = "ffmpeg"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC

    dependencies = ["cmd:ffmpeg", "cmd:ffprobe"]
    install_instructions = "Install FFmpeg: https://ffmpeg.org/download.html"
    agent_skills = ["ffmpeg"]

    capabilities = ["delivery_qc", "loudness_measurement", "shot_rhythm_analysis"]
    best_for = ["final pass on any render before it is presented or published"]

    input_schema = {
        "type": "object",
        "required": ["input_path"],
        "properties": {
            "input_path": {"type": "string", "description": "Finished render to check."},
            "loudness_profile": {
                "type": "string",
                "enum": list(LOUDNESS_TARGETS),
                "default": "social",
                "description": "Delivery loudness spec to check against.",
            },
            "format": {
                "type": "string",
                "enum": list(RHYTHM_NORMS),
                "default": "short_form",
                "description": "Content format, sets shot-length norms.",
            },
            "expected": {
                "type": "object",
                "description": "Optional spec: width, height, fps.",
                "properties": {
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "fps": {"type": "number"},
                },
            },
            "intentional_holds": {
                "type": "array",
                "description": "[start, end] second ranges where freezes/silence are intended (e.g. end card).",
                "items": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
            },
            "scene_threshold": {
                "type": "number",
                "default": 10.0,
                "description": "scdet threshold (0-100); lower finds softer cuts.",
            },
        },
    }

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=1024, vram_mb=0, disk_mb=10)
    idempotency_key_fields = ["input_path", "loudness_profile", "format", "expected", "intentional_holds"]
    side_effects = []
    user_visible_verification = ["Read the failures/warnings list and fix each before delivery"]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        path = inputs["input_path"]
        if not Path(path).exists():
            return ToolResult(success=False, error=f"Input not found: {path}")
        start = time.time()
        try:
            report = self._run(path, inputs)
        except Exception as exc:  # noqa: BLE001 — surface any ffmpeg/parse failure to the agent
            return ToolResult(success=False, error=str(exc))
        return ToolResult(success=True, data=report, duration_seconds=round(time.time() - start, 2))

    # ------------------------------------------------------------------ passes
    def _run(self, path: str, inputs: dict[str, Any]) -> dict[str, Any]:
        spec = self._probe(path)
        dur = spec["duration"]
        holds = [tuple(h) for h in inputs.get("intentional_holds", [])]
        findings: list[dict[str, Any]] = []

        def add(level: str, check: str, msg: str, at: float | None = None):
            item = {"level": level, "check": check, "message": msg}
            if at is not None:
                item["at"] = round(at, 2)
            findings.append(item)

        def held(t0: float, t1: float) -> bool:
            return any(a - 0.25 <= t0 and t1 <= b + 0.25 for a, b in holds)

        # --- spec
        exp = inputs.get("expected", {})
        if exp.get("width") and (spec["width"], spec["height"]) != (exp["width"], exp.get("height")):
            add("fail", "spec", f"resolution {spec['width']}x{spec['height']} != {exp['width']}x{exp.get('height')}")
        if exp.get("fps") and abs(spec["fps"] - exp["fps"]) > 0.05:
            add("fail", "spec", f"frame rate {spec['fps']:.3f} != {exp['fps']}")
        if spec["pix_fmt"] != "yuv420p":
            add("warn", "spec", f"pixel format {spec['pix_fmt']} — use yuv420p for platform compatibility")
        if not spec["has_audio"]:
            add("fail", "audio", "no audio stream")
        # platforms re-encode; a starved upload loses detail twice (grain, gradients, text edges)
        min_kbps = 8000 if spec["width"] * spec["height"] >= 1920 * 1080 else 4000
        if spec["bitrate_kbps"] < min_kbps:
            add("warn", "spec", f"bitrate {spec['bitrate_kbps']} kbps < {min_kbps} kbps upload master — "
                "re-encode at CRF 16-18 / 12-20 Mbps")

        # --- video pass: black, freeze, cuts
        video = self._video_pass(path, inputs.get("scene_threshold", 10.0))
        for t0, t1 in video["black"]:
            edge = t0 < 0.3 or t1 > dur - 1.2
            if not edge and not held(t0, t1):
                add("fail" if t1 - t0 > 0.5 else "warn", "black", f"black frames {t0:.2f}-{t1:.2f}s", t0)
        for t0, t1 in video["freeze"]:
            if not held(t0, t1) and t1 - t0 >= 2.0:
                add("warn", "freeze", f"frozen picture {t0:.2f}-{t1:.2f}s ({t1 - t0:.1f}s) — add motion or cut", t0)

        cuts = sorted(video["cuts"])
        bounds = [0.0] + cuts + [dur]
        shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
        fmt = inputs.get("format", "short_form")
        max_avg, max_shot = RHYTHM_NORMS[fmt]
        asl = sum(shots) / len(shots) if shots else dur
        longest = max(shots) if shots else dur
        li = shots.index(longest) if shots else 0
        rhythm = {
            "cuts": len(cuts),
            "cuts_per_minute": round(len(cuts) / dur * 60, 1) if dur else 0,
            "average_shot_length": round(asl, 2),
            "longest_shot": round(longest, 2),
            "longest_shot_starts_at": round(bounds[li], 2),
        }
        if asl > max_avg:
            add("warn", "rhythm", f"average shot {asl:.1f}s > {max_avg}s norm for {fmt} — consider more cuts/punch-ins/B-roll")
        if longest > max_shot:
            add("warn", "rhythm", f"longest uninterrupted shot {longest:.1f}s at {bounds[li]:.1f}s > {max_shot}s for {fmt} "
                "(fine if motion graphics change inside it — verify visually)", bounds[li])

        # --- audio pass: loudness, silence
        audio = self._audio_pass(path) if spec["has_audio"] else {}
        prof = inputs.get("loudness_profile", "social")
        target, tol, tp_max = LOUDNESS_TARGETS[prof]
        if audio:
            lufs, tp = audio["integrated_lufs"], audio["true_peak_dbtp"]
            if lufs is not None and abs(lufs - target) > tol:
                add("fail" if abs(lufs - target) > 3 else "warn", "loudness",
                    f"integrated {lufs:.1f} LUFS vs target {target} ±{tol} ({prof})")
            if tp is not None and tp > tp_max:
                add("fail", "loudness", f"true peak {tp:.1f} dBTP > {tp_max} dBTP — risk of clipping after platform transcode")
            for t0, t1 in audio["silence"]:
                if t0 > 0.5 and t1 < dur - 1.0 and not held(t0, t1):
                    add("warn", "dead_air", f"silence {t0:.2f}-{t1:.2f}s ({t1 - t0:.1f}s) — fill with room tone/music or tighten", t0)

        verdict = "fail" if any(f["level"] == "fail" for f in findings) else (
            "pass_with_warnings" if findings else "pass")
        return {
            "verdict": verdict,
            "input": path,
            "spec": spec,
            "loudness": {k: audio.get(k) for k in ("integrated_lufs", "loudness_range_lu", "true_peak_dbtp")}
            | {"target_lufs": target, "max_true_peak": tp_max, "profile": prof},
            "rhythm": rhythm | {"format": fmt, "norm_max_average": max_avg, "norm_max_shot": max_shot},
            "cut_times": [round(c, 2) for c in cuts],
            "findings": findings,
        }

    def _probe(self, path: str) -> dict[str, Any]:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
            capture_output=True, text=True, check=True,
        ).stdout
        info = json.loads(out)
        v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
        a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
        if v is None:
            raise ValueError("no video stream")
        num, den = (v.get("avg_frame_rate") or "0/1").split("/")
        return {
            "width": v["width"], "height": v["height"],
            "fps": float(num) / float(den) if float(den) else 0.0,
            "pix_fmt": v.get("pix_fmt"), "video_codec": v.get("codec_name"),
            "audio_codec": a.get("codec_name") if a else None,
            "sample_rate": int(a["sample_rate"]) if a else None,
            "has_audio": a is not None,
            "duration": float(info["format"]["duration"]),
            "bitrate_kbps": round(int(info["format"].get("bit_rate", 0)) / 1000),
        }

    @staticmethod
    def _ffmpeg_log(args: list[str]) -> str:
        proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args, "-f", "null", "-"],
                              capture_output=True, text=True)
        return proc.stderr

    def _video_pass(self, path: str, threshold: float) -> dict[str, list]:
        log = self._ffmpeg_log(["-i", path, "-an", "-vf",
                                f"blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-60dB:d=1.0,scdet=threshold={threshold}"])
        black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]
        fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
        fe = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", log)]
        cuts = [float(t) for t in re.findall(r"lavfi\.scd\.time: ([\d.]+)", log)]
        return {"black": black, "freeze": list(zip(fs, fe)), "cuts": cuts}

    def _audio_pass(self, path: str) -> dict[str, Any]:
        log = self._ffmpeg_log(["-i", path, "-vn", "-af", "ebur128=peak=true,silencedetect=n=-45dB:d=1.2"])
        summary = log[log.rfind("Summary:"):] if "Summary:" in log else ""

        def grab(pattern: str):
            m = re.search(pattern, summary, re.S)
            return float(m.group(1)) if m else None
        ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
        se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
        return {
            "integrated_lufs": grab(r"I:\s+(-?[\d.]+) LUFS"),
            "loudness_range_lu": grab(r"LRA:\s+(-?[\d.]+) LU"),
            "true_peak_dbtp": grab(r"True peak:.*?Peak:\s+(-?[\d.]+) dBFS"),
            "silence": list(zip(ss, se)),
        }
