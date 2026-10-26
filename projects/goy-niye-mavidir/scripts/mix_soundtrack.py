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

# (time s, sfx name, gain dB). el_* are ElevenLabs one-shots (assets/sfx/el_*.wav, peak-normalised);
# start times are offset so each sound's peak lands on its cue: whoosh peak +0.15 s, riser peak +1.8 s.
SFX = [
    (2.40, "el_pop", -9),                                          # QARADIR (word at 2.46)
    (3.15, "el_whoosh", -16),                                      # punch-in 3.3
    (5.85, "el_whoosh", -8),                                       # cut -> Mars 6.0
    (8.21, "el_pop", -10), (8.79, "el_pop", -11),                  # SARIMTIL / QƏHVƏYİDİR
    (9.15, "el_whoosh", -16),                                      # punch-in 9.3
    (11.85, "el_whoosh", -8),                                      # cut -> Earth 12.0
    (13.50, "el_pop", -9), (14.02, "el_hit", -13),                 # MAVİDİR? + question mark
    (16.85, "el_whoosh", -8),                                      # cut -> light 17.0
    (17.30, "whoosh_short", -15),                                  # beam enters
    (20.00, "el_shimmer", -8),                                     # prism split on "amma içində"
    (22.85, "el_whoosh", -8),                                      # cut -> scattering 23.0
    (23.30, "tick", -14), (23.55, "tick", -15), (23.80, "tick", -14), (24.05, "tick", -16),
    (25.20, "el_shimmer", -16),                                    # blue scatters on "mavi işığı"
    (27.15, "whoosh_short", -14),                                  # red ray on "qırmızıdan"
    (28.42, "el_hit", -8),                                         # ×4 on "dörd"
    (30.85, "el_whoosh", -8),                                      # cut -> comparison 31.0
    (31.70, "pop_low", -11), (34.65, "pop_low", -11), (36.60, "el_pop", -9),
    (37.85, "el_whoosh", -8),                                      # cut -> Mars sunset 38.0
    (39.20, "el_riser", -10), (40.92, "el_hit", -6),               # riser peaks into MAVİDİR! + punch-in
    (42.85, "el_whoosh", -8),                                      # cut -> outro 43.0
    (44.88, "el_shimmer", -11),                                    # "atmosferin"
    (45.95, "el_pop", -14), (46.10, "el_pop", -14), (46.25, "el_pop", -13),
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
    graph.append(f"[duck][fx][vo]amix=inputs=3:normalize=0,loudnorm=I=-13.2:TP=-1.0:LRA=9,"
                 f"aresample=48000,alimiter=limit=0.84:level=0,atrim=0:{DUR}[out]")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", ";\n".join(graph), "-map", "[out]", "-ar", "48000", "-ac", "2", str(OUT)]
    subprocess.run(cmd, check=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
