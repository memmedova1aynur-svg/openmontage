"""Premix the 48 s soundtrack for 'Göy niyə mavidir'.

- Narration (assets/audio/gemini/vo_s*.wav, Gemini TTS) finished with the
  `vo_master` chain from tools/audio/audio_enhance.py, placed at scene cues
- Music time-stretched to the programme, sidechain-ducked under the voice
- SFX and per-world ambience from assets/sfx (scripts/make_sfx.py), cue list below
- Delivered at -14 LUFS / <= -1 dBTP (social spec, checked by delivery_qc)

HyperFrames only supports a static data-volume, so all level automation lives here.
Usage: python mix_soundtrack.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parents[1]))
from tools.audio.audio_enhance import PRESETS  # noqa: E402

DUR = 48.0
OUT = ROOT / "hyperframes" / "assets" / "soundtrack.wav"

# narration cue (s) per scene s1..s8
VO_CUES = [0.5, 6.4, 12.4, 17.4, 23.4, 31.4, 38.4, 43.6]

# (time s, sfx name, gain dB). Whooshes start ~0.38 s early so their peak lands on the cut.
SFX = [
    (1.30, "pop", -8),                                         # QARADIR slam
    (3.10, "whoosh_short", -12),                               # punch-in to Earth
    (5.62, "whoosh", -9),                                      # -> Mars
    (7.20, "pop", -10), (7.50, "pop_low", -10),                # SARIMTIL / QƏHVƏYİDİR
    (9.10, "whoosh_short", -13),                               # punch-in on rocks
    (11.62, "whoosh", -9),                                     # -> Earth
    (13.00, "pop", -9), (13.50, "hit", -11),                   # MAVİDİR? + question mark
    (16.62, "whoosh", -9),                                     # -> light
    (17.30, "riser", -16), (18.40, "shimmer", -9),             # beam, spectrum fans out
    (22.62, "whoosh", -9),                                     # -> scattering
    (23.30, "tick", -14), (23.55, "tick", -15), (23.80, "tick", -14), (24.05, "tick", -16),
    (24.20, "whoosh_short", -15),                              # red ray passes straight through
    (27.40, "hit", -9),                                        # ×4
    (30.62, "whoosh", -9),                                     # -> comparison
    (32.40, "pop_low", -11), (33.60, "pop_low", -11), (35.00, "pop", -9),
    (37.62, "whoosh", -9),                                     # -> Mars sunset
    (38.20, "riser", -13), (39.70, "hit", -8),                 # ... MAVİDİR!
    (40.60, "whoosh_short", -14),                              # punch-in on the blue halo
    (42.62, "whoosh", -9),                                     # -> outro
    (43.90, "shimmer", -11),
    (44.40, "pop", -13), (44.55, "pop", -13), (44.70, "pop", -12),
]

# (start, end, ambience, gain dB)
AMB = [
    (0.0, 6.0, "amb_space", -10), (6.0, 12.0, "amb_mars_wind", -12), (12.0, 17.0, "amb_air", -14),
    (17.0, 23.0, "amb_space", -12), (23.0, 31.0, "amb_air", -16), (31.0, 38.0, "amb_space", -16),
    (38.0, 43.0, "amb_mars_wind", -12), (43.0, 48.0, "amb_space", -12),
]


def main() -> None:
    vo_chain = PRESETS["vo_master"]["af"]
    inputs: list[str] = []
    graph: list[str] = []
    voice, fx = [], []

    def add_input(path: Path) -> int:
        inputs.extend(["-i", str(path)])
        return len(inputs) // 2 - 1

    for i, cue in enumerate(VO_CUES, 1):
        k = add_input(ROOT / "assets" / "audio" / "gemini" / f"vo_s{i}.wav")
        graph.append(f"[{k}:a]{vo_chain},aformat=channel_layouts=mono,adelay={int(cue * 1000)}[v{i}]")
        voice.append(f"[v{i}]")
    for j, (t, name, gain) in enumerate(SFX):
        k = add_input(ROOT / "assets" / "sfx" / f"{name}.wav")
        graph.append(f"[{k}:a]aresample=48000,volume={gain}dB,adelay={int(t * 1000)}[s{j}]")
        fx.append(f"[s{j}]")
    for j, (a, b, name, gain) in enumerate(AMB):
        k = add_input(ROOT / "assets" / "sfx" / f"{name}.wav")
        graph.append(f"[{k}:a]aresample=48000,atrim=0:{b - a + 0.4},afade=t=in:d=0.25,"
                     f"afade=t=out:st={b - a + 0.05}:d=0.35,volume={gain}dB,adelay={int(a * 1000)}[a{j}]")
        fx.append(f"[a{j}]")

    music = ROOT / "assets" / "music" / "bgm.mp3"
    mlen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(music)], capture_output=True, text=True, check=True).stdout)
    k = add_input(music)
    tempo = round(mlen / (DUR + 0.3), 4)
    graph.append(f"[{k}:a]aresample=48000,atempo={tempo},volume=0.42,afade=t=in:d=0.6,"
                 f"afade=t=out:st={DUR - 2}:d=1.9,apad=whole_dur={DUR}[mus]")

    graph.append(f"{''.join(voice)}amix=inputs={len(voice)}:normalize=0,apad=whole_dur={DUR},"
                 f"aformat=channel_layouts=stereo,asplit[vo][key]")
    graph.append(f"{''.join(fx)}amix=inputs={len(fx)}:normalize=0,apad=whole_dur={DUR},aformat=channel_layouts=stereo[fx]")
    graph.append("[mus][key]sidechaincompress=threshold=0.03:ratio=8:attack=25:release=420[duck]")
    graph.append(f"[duck][fx][vo]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,"
                 f"aresample=48000,alimiter=limit=0.84:level=0,atrim=0:{DUR}[out]")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", ";\n".join(graph), "-map", "[out]", "-ar", "48000", "-ac", "2", str(OUT)]
    subprocess.run(cmd, check=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
