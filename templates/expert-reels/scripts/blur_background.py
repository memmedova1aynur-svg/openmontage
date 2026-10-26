#!/usr/bin/env python3
"""Softly blur the background behind the speaker, keeping the person sharp.

Usage:
    python templates/expert-reels/scripts/blur_background.py <in.mp4> <out.mp4> [--sigma 9] [--still <seconds>]

Uses MODNet portrait matting (Apache-2.0, ONNX build from huggingface.co/Xenova/modnet),
downloaded once to ~/.cache/openmontage/modnet.onnx. The matte is smoothed over time
so hair edges do not shimmer. --still writes one preview PNG instead of a video.
"""
from __future__ import annotations

import argparse
import subprocess
import urllib.request
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODEL_URL = "https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx"
MODEL = Path.home() / ".cache" / "openmontage" / "modnet.onnx"
W, H = 1080, 1920
MW, MH = 512, 896  # matting resolution (multiples of 32, same 9:16-ish aspect)


def load_model() -> ort.InferenceSession:
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    return ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])


def matte(sess: ort.InferenceSession, rgb: np.ndarray) -> np.ndarray:
    x = cv2.resize(rgb, (MW, MH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
    m = sess.run(None, {"input": x})[0][0, 0]
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)


def composite(rgb: np.ndarray, m: np.ndarray, sigma: float) -> np.ndarray:
    # blur at quarter size (fast, and a smoother bokeh-like falloff)
    small = cv2.resize(rgb, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bg = cv2.resize(cv2.GaussianBlur(small, (0, 0), sigma / 4), (W, H), interpolation=cv2.INTER_LINEAR)
    a = m[..., None]
    return (rgb * a + bg * (1 - a)).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--sigma", type=float, default=9.0, help="background blur strength (px at 1080p)")
    ap.add_argument("--still", type=float, default=None)
    args = ap.parse_args()
    sess = load_model()

    if args.still is not None:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(args.still), "-i", args.src, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True,
        ).stdout
        rgb = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        cv2.imwrite(args.dst, cv2.cvtColor(composite(rgb, matte(sess, rgb), args.sigma), cv2.COLOR_RGB2BGR))
        return

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", args.src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
         "-i", args.src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "copy", args.dst],
        stdin=subprocess.PIPE,
    )
    prev = None
    n = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        m = matte(sess, rgb)
        prev = m if prev is None else 0.6 * m + 0.4 * prev  # temporal smoothing against edge shimmer
        enc.stdin.write(composite(rgb, prev, args.sigma).tobytes())
        n += 1
        if n % 300 == 0:
            print(f"{n} frames", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"done: {n} frames -> {args.dst}")


if __name__ == "__main__":
    main()
