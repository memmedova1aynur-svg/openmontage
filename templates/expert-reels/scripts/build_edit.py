#!/usr/bin/env python3
"""Build public/edit.json (+ synthesized SFX) for the expert-reels template.

Usage:
    python templates/expert-reels/scripts/build_edit.py <spec.json> <remotion_workspace_dir>

The spec names the expert profile (brand theme), the word-timed transcript,
zoom keys, keyword pills, cutaways and per-video style picks. See
templates/expert-reels/README.md for the format.
"""
from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

TEMPLATE = Path(__file__).resolve().parents[1]

DEFAULT_STYLE = {
    "captions": "stroke",
    "pills": "top-card",
    "backdrop": "dots",
    "pipShape": "circle",
    "pipCorner": "br",
    "pops": "dark",
}
DEFAULT_PIP = {"focus": [560, 895], "radius": 210, "scale": 0.69}


def caption_pages(words: list[dict], max_words: int, max_chars: int) -> list[dict]:
    """Group words into caption pages. A page never runs past the end of a
    sentence or a comma, so every sentence starts on a fresh line."""
    pages, cur = [], []
    for w in words:
        txt = w["word"].strip()
        if cur and (len(cur) >= max_words or len(" ".join([x["w"] for x in cur] + [txt])) > max_chars):
            pages.append(cur)
            cur = []
        cur.append({"w": txt, "s": w["start"], "e": w["end"]})
        if txt[-1] in ".?!,:;…»" and not (txt[-1] == "»" and len(txt) > 1 and txt[-2] not in ".?!,"):
            pages.append(cur)
            cur = []
    if cur:
        pages.append(cur)
    out = []
    for i, p in enumerate(pages):
        nxt = pages[i + 1][0]["s"] if i + 1 < len(pages) else p[-1]["e"] + 0.6
        out.append({"start": p[0]["s"], "end": min(nxt, p[-1]["e"] + 0.7), "words": p})
    return out


def auto_sfx(spec: dict, cutaways: list[dict], overlays: list[dict]) -> list[dict]:
    # SFX only when the approved storyboard asked for them ("sfx_level": "minimal" | "full")
    if spec.get("sfx_level", "none") == "none":
        return list(spec.get("extra_sfx", []))
    # keyword pops get a light pop; cards get a whoosh
    sfx = [
        {"t": round(o["in"], 2), "src": "sfx/pop.wav", "vol": 0.3} if o["kind"] == "pop"
        else {"t": round(o["in"] - 0.12, 2), "src": "sfx/whoosh.wav", "vol": 0.45}
        for o in overlays
    ]
    for c in cutaways:
        sfx.append({"t": round(c["in"] - 0.12, 2), "src": "sfx/whoosh.wav", "vol": 0.5})
        if c["kind"] in ("pip", "full"):
            sfx.append({"t": round(c["out"] - 0.15, 2), "src": "sfx/whoosh.wav", "vol": 0.45})
            for pn in c.get("panels", [])[1:]:
                sfx.append({"t": round(pn["at"] - 0.1, 2), "src": "sfx/whoosh.wav", "vol": 0.3})
            for pn in c.get("panels", []):
                for t in pn["props"].get("times", []):
                    sfx.append({"t": t, "src": "sfx/pop.wav", "vol": 0.22})
        if c["kind"] == "comment":
            pr = c["props"]
            n = len(pr["keyword"])
            step = (pr["type_end"] - pr["type_start"]) / max(1, n)
            sfx += [{"t": round(pr["type_start"] + k * step, 3), "src": "sfx/tick.wav", "vol": 0.3} for k in range(n)]
            sfx.append({"t": pr["send"], "src": "sfx/ding.wav", "vol": 0.35})
    busy = [c for c in cutaways if c["kind"] in ("pip", "full")]
    for t, _, k in spec["zoom"]:
        if k == "punch":
            sfx.append({"t": t, "src": "sfx/hit.wav", "vol": 0.55})
        elif (
            k == "push"
            and spec.get("sfx_level") != "minimal"
            and not any(abs(t - o["in"]) < 0.8 for o in overlays)
            and not any(c["in"] - 0.2 <= t <= c["out"] for c in busy)
        ):
            sfx.append({"t": t, "src": "sfx/pop.wav", "vol": 0.35})
    if spec.get("sfx_level") == "minimal":  # calmer edits: quieter, fewer cues
        sfx = [{**s, "vol": round(s["vol"] * 0.7, 2)} for s in sfx]
    sfx += spec.get("extra_sfx", [])
    return sorted(sfx, key=lambda s: s["t"])


def synth_sfx(out_dir: Path) -> None:
    """Royalty-free SFX synthesized from scratch (whoosh, pop, hit, tick, ding)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    sr = 48000
    rng = np.random.default_rng(7)

    def save(name: str, x: np.ndarray) -> None:
        x = x / np.max(np.abs(x)) * 0.9
        x = np.stack([x, x], 1)
        with wave.open(str(out_dir / f"{name}.wav"), "w") as f:
            f.setnchannels(2)
            f.setsampwidth(2)
            f.setframerate(sr)
            f.writeframes((x * 32767).astype(np.int16).tobytes())

    def bandpass_sweep(dur: float, f0: float, f1: float) -> np.ndarray:
        n = int(sr * dur)
        noise = rng.standard_normal(n)
        out = np.zeros(n)
        y1 = y2 = 0.0
        for i in range(n):
            w = 2 * np.pi * f0 * (f1 / f0) ** (i / n) / sr
            r = 0.97
            y = (1 - r) * noise[i] + 2 * r * np.cos(w) * y1 - r * r * y2
            out[i] = y
            y2, y1 = y1, y
        return out

    t = np.arange(int(sr * 0.45)) / sr
    save("whoosh", bandpass_sweep(0.45, 350, 3800) * np.sin(np.pi * t / 0.45) ** 2 * np.exp(-1.5 * t))
    t = np.arange(int(sr * 0.12)) / sr
    save("pop", np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 25) + 250) / sr) * np.exp(-t * 40))
    t = np.arange(int(sr * 0.35)) / sr
    thump = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t * 12) + 45) / sr) * np.exp(-t * 11)
    save("hit", thump + rng.standard_normal(len(t)) * np.exp(-t * 160) * 0.35)
    t = np.arange(int(sr * 0.03)) / sr
    save("tick", rng.standard_normal(len(t)) * np.exp(-t * 400) + 0.5 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 300))
    t = np.arange(int(sr * 1.1)) / sr
    partials = [(1318, 1, 4), (2637, 0.45, 6), (3951, 0.2, 9), (1976, 0.25, 5)]
    save("ding", sum(a * np.sin(2 * np.pi * fr * t) * np.exp(-t * d) for fr, a, d in partials))
    # pen-stroke scratch for strike-throughs: short high band of noise with a quick swell
    t = np.arange(int(sr * 0.28)) / sr
    save("scratch", bandpass_sweep(0.28, 2600, 5200) * np.sin(np.pi * t / 0.28) ** 1.5)
    # topic sounds (all synthesized): scissors snip, clock tick-tock, spoon clink, fabric swish,
    # soft door knock, gentle chime
    def env(n, k): return np.exp(-np.arange(n) / sr * k)
    n = int(sr * 0.06)
    click = rng.standard_normal(n) * env(n, 120) + np.sin(2 * np.pi * 3200 * np.arange(n) / sr) * env(n, 90) * 0.6
    snip = np.zeros(int(sr * 0.32)); snip[:n] += click; snip[int(sr * 0.16):int(sr * 0.16) + n] += click * 0.9
    save("snip", snip)
    n = int(sr * 0.03)
    tk = np.sin(2 * np.pi * 1900 * np.arange(n) / sr) * env(n, 220); tc = np.sin(2 * np.pi * 1400 * np.arange(n) / sr) * env(n, 220)
    tt = np.zeros(int(sr * 0.75)); tt[:n] += tk; tt[int(sr * 0.38):int(sr * 0.38) + n] += tc
    save("ticktock", tt)
    t = np.arange(int(sr * 0.5)) / sr
    save("clink", (np.sin(2 * np.pi * 2950 * t) + 0.5 * np.sin(2 * np.pi * 4420 * t) + 0.3 * np.sin(2 * np.pi * 6210 * t)) * np.exp(-t * 9))
    t = np.arange(int(sr * 0.35)) / sr
    save("swish", bandpass_sweep(0.35, 1800, 700) * np.sin(np.pi * t / 0.35) ** 2)
    n = int(sr * 0.12)
    knock1 = np.sin(2 * np.pi * np.cumsum(np.full(n, 180.0)) / sr) * env(n, 40) + rng.standard_normal(n) * env(n, 300) * 0.3
    kk = np.zeros(int(sr * 0.4)); kk[:n] += knock1; kk[int(sr * 0.2):int(sr * 0.2) + n] += knock1 * 0.85
    save("knock", kk)
    t = np.arange(int(sr * 1.4)) / sr
    save("chime", sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in [(1046.5, 1, 3), (1568, 0.6, 3.5), (2093, 0.35, 4.5)]))
    # soft low thump for a closing key line (no click, no noise burst like "hit")
    t = np.arange(int(sr * 0.4)) / sr
    save("thump", np.sin(2 * np.pi * np.cumsum(110 * np.exp(-t * 6) + 55) / sr) * (1 - np.exp(-t * 300)) * np.exp(-t * 9))


def main() -> None:
    spec_path, ws = Path(sys.argv[1]), Path(sys.argv[2])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    expert = json.loads((TEMPLATE / "experts" / f"{spec['expert']}.json").read_text(encoding="utf-8"))
    if expert.get("status") in ("inactive", "paused"):
        sys.exit(f"{spec['expert']} is {expert['status']}: no edit tasks for this profile until the user activates it")
    # a per-video theme (e.g. the colour column chosen in the storyboard) overrides the profile's default
    if "theme" in spec:
        expert["theme"] = {**expert.get("theme", {}), **spec["theme"]}
    if "theme" not in expert:
        sys.exit(f"{spec['expert']} has no default theme ({expert.get('theme_source', '')}); set spec['theme'] from the approved storyboard")
    words = json.loads((spec_path.parent / spec["words"]).read_text(encoding="utf-8"))
    if words and "words" in words[0]:  # transcriber segment format
        words = [w for seg in words for w in seg["words"]]

    cap = spec.get("captions", {})
    cutaways = spec.get("cutaways", [])
    overlays = []
    for o in spec.get("overlays", []):
        if o.get("kind") == "pop" and o.get("pos") in ("l", "r") and len("".join(t for t, _ in o["parts"])) > 24:
            # a long side pop wraps to 3-4 lines and crowds the speaker; long phrases go on top
            print(f"NOTE: pop {o['id']} is long for a side position - moved to top")
            o = {**o, "pos": "t"}
        clash = next((c for c in cutaways if o["in"] < c["out"] and c["in"] < o["out"]), None)
        if clash:  # a pill on top of a cutaway reads as clutter; the cutaway wins
            print(f"WARN: pill {o['id']} overlaps cutaway {clash['id']} - dropped")
        else:
            overlays.append(o)
    # the footage decides the length; spec["duration"] is only a fallback
    footage = ws / "public" / spec.get("video", "base.mp4")
    duration = spec.get("duration", 0)
    if footage.exists():
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(footage)],
                               capture_output=True, text=True)
        if probe.returncode == 0 and probe.stdout.strip():
            # whole frames only, so the edit ends exactly where the footage ends
            duration = int(float(probe.stdout.strip()) * 30) / 30
    edit = {
        "duration": duration,
        "video": spec.get("video", "base.mp4"),
        "pillTop": spec.get("pill_top", 300),
        "plate": spec.get("plate"),
        "tabs": spec.get("tabs", []),
        "theme": expert["theme"],
        "style": {**DEFAULT_STYLE, **expert.get("style", {}), **spec.get("style", {})},
        "pip": {**DEFAULT_PIP, **spec.get("pip", {})},
        "pages": caption_pages(words, cap.get("max_words", 3), cap.get("max_chars", 17)),
        "zoom": [{"t": t, "s": s, "k": k} for t, s, k in spec["zoom"]],
        "overlays": overlays,
        "cutaways": cutaways,
        "sfx": auto_sfx(spec, cutaways, overlays),
    }
    pub = ws / "public"
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "edit.json").write_text(json.dumps(edit, ensure_ascii=False, indent=1), encoding="utf-8")
    synth_sfx(pub / "sfx")
    print(f"edit.json: {len(edit['pages'])} caption pages, {len(overlays)} pills, "
          f"{len(cutaways)} cutaways, {len(edit['sfx'])} sfx cues; style={edit['style']}")


if __name__ == "__main__":
    main()
