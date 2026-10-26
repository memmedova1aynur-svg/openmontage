---
name: mms-tts
description: Free, offline narration in 1000+ languages with Meta MMS-TTS (VITS, run via sherpa-onnx). Use when the user wants zero-cost narration in a language Piper and the paid providers don't cover well — especially Azerbaijani (azj-script_latin) — and accepts a plain, non-expressive voice.
---

# Meta MMS-TTS (`mms_tts` tool)

Runs Meta's Massively Multilingual Speech VITS checkpoints locally through
`sherpa-onnx`. No API key, no GPU, no torch. ~0.5 s per sentence on CPU.

```bash
pip install sherpa-onnx onnxruntime scipy
```

Models (~110 MB each) download on first use from
`huggingface.co/willwade/mms-tts-multilingual-models-onnx/<lang>/` into
`~/.cache/openmontage/mms-tts/<lang>/`.

## Inputs

| Field | Default | Notes |
|---|---|---|
| `text` | — | Plain text. Write it with normal punctuation; the tool splits on `. ! ? …` and spaced dashes |
| `language` | `azj-script_latin` | Any MMS code: `tur`, `kaz`, `uzb-script_latin`, `rus`, `azj-script_cyrillic`, … |
| `speed` | `1.0` | 0.9–0.95 sounds calmer and clearer for explainers |
| `noise_scale` | `0.667` | Lower = flatter, higher = livelier but less stable |
| `sentence_silence` | `0.35` | Pause inserted between sentences (the model itself ignores punctuation) |

Output: 16 kHz mono WAV, peak-normalized.

## Writing text for MMS

- **The vocabulary has no punctuation.** Pauses come only from the sentence
  split, so phrase-level pauses need their own sentence: "Qırmızıdan təxminən
  dörd dəfə çox." as a separate sentence instead of after a dash.
- **Spell numbers as words** ("dörd", not "4"). The tool spells single digits as a
  fallback, but "45" becomes "dörd beş", so write "qırx beş".
- Capitals are lowercased (the tool maps `İ→i`, `I→ı` for Azerbaijani/Turkish).
- Audio tags like `[excited]` are stripped. MMS has no emotion control.
- Generate **one file per script section** and time each scene to the clip's
  measured length. Don't stretch audio to fit a fixed scene.

## Quality expectations

Intelligible, neutral, slightly synthetic. Good enough for explainers and
social clips, not for ads or broadcast. If the user wants expressive delivery,
offer a paid provider (ElevenLabs/Azure have Azerbaijani voices) and let them
decide.

## Licensing

MMS weights are **CC-BY-NC-4.0**: non-commercial use only. Tell the user this
before using the tool on a commercial or monetized project.

## Mastering for video

16 kHz is thin on its own. Before muxing:

```bash
ffmpeg -i vo.wav -af "aresample=48000,highpass=f=70,equalizer=f=3500:t=q:w=1:g=3,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-16:TP=-1.5" vo_master.wav
```

Duck the music under narration (about −14 dB) with a timeline volume tween or `audio_mixer`.
