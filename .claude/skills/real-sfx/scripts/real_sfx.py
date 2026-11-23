#!/usr/bin/env python3
"""Real SFX: place real sound effects on a video at exact moments.

  analyze  VIDEO [-o cues.json] [--frames DIR] [--threshold 0.35]
           Finds scene cuts and writes a cue list (time + suggested type) and,
           optionally, one still per cue so the agent can look and decide.
  place    VIDEO CUES [-o out.mp4] [--lib assets/sfx] [--earshot]
           Resolves every cue to a sound file, aligns it, builds a separate
           SFX stem (WAV) and mixes it under the existing voice/music
           (sidechain ducking), video stream copied untouched.
  library  [--lib assets/sfx]   lists the sounds available per type.

Cue format (JSON list or {"cues": [...]}):
  {"t": 1.20, "type": "whoosh", "gain_db": -14, "anchor": "peak", "file": null, "note": "cut"}
  t        seconds in the video where the sound must land
  type     library folder / keyword (whoosh, hit, click, pop, riser, ding, swipe, typing ...)
  file     optional explicit path (wins over type)
  anchor   "peak": the loudest moment lands on t (default for whoosh/riser/swipe/impact)
           "onset": the start lands 10 ms before t (default for everything else)
  gain_db  level of this sound in the stem (default -14 dB)

Only stdlib + ffmpeg/ffprobe are required.
"""
from __future__ import annotations

import argparse
import array
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SR = 48000
AUDIO_EXT = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".webm", ".aiff", ".aif"}
PEAK_TYPES = {"whoosh", "swoosh", "swipe", "riser", "impact", "boom", "transition", "reverse"}
ALIASES = {
    "swoosh": ["whoosh", "swipe"], "swipe": ["whoosh", "swoosh"], "transition": ["whoosh"],
    "impact": ["hit", "boom"], "hit": ["impact", "thud"], "boom": ["impact", "hit"],
    "tap": ["click"], "click": ["tap", "ui"], "pop": ["bubble", "click"], "ding": ["bell", "chime", "notify"],
    "typing": ["keyboard", "keypress"], "riser": ["rise", "whoosh"],
}


def run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=capture, text=True)


def probe_duration(path: str) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout
    return float(out.strip())


def has_audio(path: str) -> bool:
    out = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
               "-of", "csv=p=0", path]).stdout
    return bool(out.strip())


# ---------------------------------------------------------------- analyze
def detect_cuts(video: str, threshold: float) -> list[float]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-an", "-vf",
                        f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", p.stderr)]


def analyze(video: str, out: str, frames: str | None, threshold: float, min_gap: float) -> list[dict]:
    dur = probe_duration(video)
    cues, last = [], -1e9
    for t in detect_cuts(video, threshold):
        if t - last < min_gap or t < 0.15 or t > dur - 0.1:
            continue
        cues.append({"t": round(t, 3), "type": "whoosh", "gain_db": -16, "anchor": "peak",
                     "note": "scene cut (suggested; change type or delete)"})
        last = t
    if frames:
        Path(frames).mkdir(parents=True, exist_ok=True)
        for i, c in enumerate(cues):
            f = Path(frames) / f"cue{i:02d}_{c['t']:.2f}s.jpg"
            run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{c['t'] + 0.05:.3f}", "-i", video,
                 "-frames:v", "1", "-vf", "scale=360:-2", str(f)])
            c["frame"] = str(f)
    Path(out).write_text(json.dumps({"video": video, "duration": dur, "cues": cues}, indent=2))
    return cues


# ---------------------------------------------------------------- library
def library(lib: Path) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = {}
    if not lib.exists():
        return idx
    for p in sorted(lib.rglob("*")):
        if p.suffix.lower() not in AUDIO_EXT or not p.is_file():
            continue
        key = p.parent.name.lower() if p.parent != lib else re.split(r"[_\-\s.]", p.stem.lower())[0]
        idx.setdefault(key, []).append(p)
    return idx


def find_in_library(idx: dict[str, list[Path]], sfx_type: str, used: dict[str, int]) -> Path | None:
    t = sfx_type.lower()
    for key in [t] + ALIASES.get(t, []):
        files = idx.get(key) or [p for k, ps in idx.items() for p in ps if key in p.stem.lower()]
        if files:
            n = used.get(key, 0)
            used[key] = n + 1
            return files[n % len(files)]  # rotate so repeated cues don't sound identical
    return None


def earshot_bin() -> str | None:
    return os.environ.get("EARSHOT_BIN") or shutil.which("earshot")


def earshot_make(sfx_type: str, out: Path, seed: int) -> Path | None:
    exe = earshot_bin()
    if not exe:
        return None
    try:
        run([exe, "make", sfx_type, "-o", str(out), "--seed", str(seed)])
        return out
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------------- audio helpers
def to_wav(src: Path, dst: Path) -> None:
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "2", "-ar", str(SR),
         "-c:a", "pcm_s16le", str(dst)])


def peak_time(wav: Path) -> float:
    p =subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-ar", "8000",
                        "-f", "s16le", "-"], capture_output=True, check=True)
    a = array.array("h", p.stdout[: len(p.stdout) // 2 * 2])
    if not a:
        return 0.0
    # 20 ms RMS-ish envelope, take the loudest window
    win = 160
    best, best_i = -1, 0
    for i in range(0, len(a), win):
        e = sum(abs(x) for x in a[i:i + win])
        if e > best:
            best, best_i = e, i
    return (best_i + win / 2) / 8000.0


# ---------------------------------------------------------------- place
def load_cues(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text())
    cues = data["cues"] if isinstance(data, dict) else data
    return sorted(cues, key=lambda c: float(c["t"]))


def place(video: str, cues_path: str, out: str, lib: Path, use_earshot: bool, sfx_gain: float,
          duck: bool) -> dict:
    cues = load_cues(cues_path)
    if not cues:
        raise SystemExit("no cues")
    dur = probe_duration(video)
    idx = library(lib)
    used: dict[str, int] = {}
    out_p = Path(out)
    stem = out_p.with_name(out_p.stem + "_sfx.wav")
    report = out_p.with_name(out_p.stem + "_sfx_cues.json")
    tmp = Path(tempfile.mkdtemp(prefix="realsfx_"))
    resolved, missing = [], []
    try:
        for i, c in enumerate(cues):
            t = float(c["t"])
            typ = str(c.get("type") or "click")
            src = Path(c["file"]) if c.get("file") else find_in_library(idx, typ, used)
            origin = "file" if c.get("file") else "library"
            if src is None and use_earshot:
                src = earshot_make(typ, tmp / f"gen{i}.wav", seed=1000 + i)
                origin = "earshot"
            if src is None or not Path(src).exists():
                missing.append({"t": t, "type": typ})
                continue
            wav = tmp / f"c{i}.wav"
            to_wav(Path(src), wav)
            anchor = c.get("anchor") or ("peak" if typ.lower() in PEAK_TYPES else "onset")
            offset = peak_time(wav) if anchor == "peak" else 0.010
            start = max(0.0, t - offset)
            resolved.append({**c, "t": t, "type": typ, "anchor": anchor, "source": str(src), "origin": origin,
                             "start": round(start, 4), "gain_db": float(c.get("gain_db", -14)), "_wav": str(wav)})
        if not resolved:
            raise SystemExit(f"no sound found for any cue (missing: {missing}). "
                             f"Fill {lib}/<type>/ via openverse-sfx or earshot, or pass --earshot.")
        # 1) SFX stem: every sound delayed to its start, summed without normalization
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for r in resolved:
            cmd += ["-i", r["_wav"]]
        parts = []
        for k, r in enumerate(resolved):
            ms = int(round(r["start"] * 1000))
            parts.append(f"[{k}:a]volume={r['gain_db'] + sfx_gain:.1f}dB,adelay={ms}|{ms}[s{k}]")
        mix_in = "".join(f"[s{k}]" for k in range(len(resolved)))
        parts.append(f"{mix_in}amix=inputs={len(resolved)}:normalize=0:dropout_transition=0,"
                     f"apad,atrim=0:{dur:.3f},alimiter=limit=0.89[out]")
        cmd += ["-filter_complex", ";".join(parts), "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_s24le", str(stem)]
        run(cmd)
        # 2) final mix: original audio stays on top; SFX ducks while someone speaks
        if has_audio(video):
            if duck:
                fc = ("[0:a]aresample=48000,asplit=2[main][key];"
                      "[1:a][key]sidechaincompress=threshold=0.03:ratio=3:attack=10:release=300[sfxd];"
                      "[main][sfxd]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
            else:
                fc = "[0:a]aresample=48000[main];[main][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]"
        else:
            fc = "[1:a]anull[a]"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", str(stem), "-filter_complex", fc,
             "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", "-shortest", str(out_p)])
        for r in resolved:
            r.pop("_wav", None)
        rep = {"video": video, "output": str(out_p), "sfx_stem": str(stem), "placed": resolved, "missing": missing}
        report.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
        return rep
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("analyze")
    a1.add_argument("video")
    a1.add_argument("-o", "--out", default="cues.json")
    a1.add_argument("--frames", help="folder for one still per cue")
    a1.add_argument("--threshold", type=float, default=0.35, help="scene-change sensitivity (lower = more cuts)")
    a1.add_argument("--min-gap", type=float, default=0.5)
    a2 = sub.add_parser("place")
    a2.add_argument("video")
    a2.add_argument("cues")
    a2.add_argument("-o", "--out")
    a2.add_argument("--lib", default="assets/sfx")
    a2.add_argument("--earshot", action="store_true", help="generate sounds the library lacks with earshot")
    a2.add_argument("--sfx-gain", type=float, default=0.0, help="dB added to the whole SFX layer")
    a2.add_argument("--no-duck", action="store_true")
    a3 = sub.add_parser("library")
    a3.add_argument("--lib", default="assets/sfx")
    a = ap.parse_args(argv)
    if a.cmd == "analyze":
        cues = analyze(a.video, a.out, a.frames, a.threshold, a.min_gap)
        print(f"{len(cues)} cue(s) -> {a.out}")
        for c in cues:
            print(f"  {c['t']:7.2f}s  {c['type']}")
    elif a.cmd == "place":
        out = a.out or str(Path(a.video).with_name(Path(a.video).stem + "_sfx.mp4"))
        rep = place(a.video, a.cues, out, Path(a.lib), a.earshot, a.sfx_gain, not a.no_duck)
        print(f"video: {rep['output']}\nstem:  {rep['sfx_stem']}")
        for r in rep["placed"]:
            print(f"  {r['t']:7.2f}s  {r['type']:<8} {r['origin']:<8} {Path(r['source']).name}")
        for m in rep["missing"]:
            print(f"  {m['t']:7.2f}s  {m['type']:<8} MISSING (no file in library)")
    else:
        idx = library(Path(a.lib))
        if not idx:
            print(f"library {a.lib} is empty")
        for k, ps in sorted(idx.items()):
            print(f"{k:<12} {len(ps):3d}  " + ", ".join(p.name for p in ps[:4]) + (" ..." if len(ps) > 4 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
