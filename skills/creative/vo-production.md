# VO Production — Directing and Finishing Narration

## When to Use

Every video with narration, human or TTS. Works with
`meta/voice-performance-director.md` (the per-section performance contract);
this skill covers how to direct a TTS take, verify it, and finish it so it
sounds like a booth recording rather than a text-to-speech file.

## 1. Write for the ear

- Short sentences (≤ 15 words), one idea each. Spoken language, not
  written: contractions, direct "you", no parentheses.
- Numbers and symbols written as spoken words in the narration text
  ("təxminən dörd dəfə", not "~4x"); keep the symbol for on-screen text.
- Put the key word at the **end** of the sentence — that's where stress lands
  naturally.
- Read the script aloud at target speed; cut whatever you trip on.

| Content | Words per minute |
|---|---|
| Ads / hype short-form | 160–185 |
| Explainer / educational short-form | 145–165 |
| Documentary / long-form | 125–145 |

## 2. Direct the TTS like an actor

Give the engine a *role and a situation*, not adjectives. Weak: "energetic,
natural". Strong: "You are a science YouTuber telling a friend a surprising
fact. Lean in on the contrast; slight smile in the voice; slow down on the
answer."

Provider levers:
- **Gemini TTS** (`gemini_tts`): `style` carries role, language/accent
  instruction and per-line delivery; one call per beat so every line can be
  directed; multi-speaker `turns` for dialogue.
- **ElevenLabs**: stability 0.3–0.5 for expressive narration, style
  0.2–0.45, speaker boost on; use previous/next text for continuity.
- **OpenAI TTS**: `instructions` for tone, pacing and emphasis.
- **Azure / Google**: SSML `<break>`, `<emphasis>`, `<prosody rate>`.

Language and accent: name the language explicitly *and* say what it is not
(e.g. "Azərbaycan dili, Bakı tələffüzü — Türkiyə türkcəsi deyil"). Spell out
tricky words in the hint ("'göy', not 'gök'"). Short lines (< 6 words) drift
toward a neighbouring language most often — generate them with a longer
context line and trim, or generate 3 takes.

## 3. Takes and selection

1. Generate **2–3 takes per line** for hooks, payoffs and any short line.
2. **Verify every take by transcription** (`transcriber` locally, or a
   different model than the one that spoke): the transcript must match the
   script word for word, in the right language. A mismatch means the
   listener mishears it too.
3. Listen for: wrong stress, swallowed endings, flat questions (no rising
   intonation), unnatural breaths, clipped first syllable.
4. Pick per line, not per batch. Record the choice and why in the decision
   log.
5. Keep TTS input text plain. Ellipses ("Bəs... Yerdə") and bracketed
   delivery tags on short lines made ElevenLabs v4 repeat the first word
   ("Bəs, bəs") — direct the read through voice/style settings instead, and
   re-transcribe any take generated with tags.

## 4. Edit the voice

- Trim heads/tails to 40–80 ms before the first phoneme; 5 ms fades on every
  edit point to kill clicks.
- Pause design: 0.15–0.3 s between clauses, 0.4–0.7 s between ideas, up to
  1 s before a reveal. Vary them; identical gaps sound synthetic.
- Breaths: keep natural ones at −6 to −10 dB; never leave a hard digital
  silence (put room tone or the music bed under it).
- Assemble narration on a timeline with each line placed at its picture cue,
  not concatenated end-to-end.

## 5. Finishing chain (booth sound)

Apply in this order — `audio_enhance` preset `vo_master` implements it:

1. High-pass 70–90 Hz (rumble, plosive energy)
2. Cut mud: −2 to −4 dB around 200–300 Hz
3. Presence: +2 to +3 dB around 3–5 kHz; air: +1.5 dB shelf at 10–12 kHz
4. De-ess 5–8 kHz
5. Compression: ratio 2.5–4:1, 3–6 dB gain reduction, attack 5–15 ms, release 80–150 ms
6. Limiter / loudness: speech stem around −16 LUFS before the mix; the full
   mix lands on the delivery target (−14 LUFS social / YouTube)

TTS output is usually already clean — skip noise reduction on synthetic
voices (it creates artefacts); do use EQ/compression so it sits with music.

## 6. Mix against music

- Sidechain-duck the music 12–18 dB under the voice with 20–40 ms attack and
  300–500 ms release (`audio_mixer` `duck`, or ffmpeg `sidechaincompress`).
- Carve a small dip (−2 to −3 dB, 2–4 kHz) in the music so consonants cut
  through without making the voice louder.
- Check on phone speakers: if words disappear, the mix is wrong.

## Quality Checklist

- [ ] Every line's transcript matches the script, in the right language
- [ ] No clipped starts, swallowed endings or flat questions
- [ ] Pauses varied and designed; no digital silence
- [ ] `vo_master` (or equivalent) applied; music sidechain-ducked
- [ ] Mix measured at delivery loudness (`delivery_qc`)
