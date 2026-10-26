## Editor QC — v3, Round 1

- delivery_qc (explainer, social): pass_with_warnings — -14.3 LUFS, -1.4 dBTP, 16.4 Mbps, yuv420p, no black/frozen frames, no dead air
- Rhythm: 7 scene cuts + 3 same-plate punch-ins (3.3, 9.3, 40.8 s; below scdet threshold) → effective ASL ≈ 4.4 s.
  Justified warning: "average shot 6.0 s" counts scene cuts only.
- Rubric: hook 4, story 4, rhythm 4, picture 4, typography 4, voice 3, sound 4, finishing 5
- Fixed vs v2: black flashes between scenes (fades → straight cuts), dead-feeling transitions (whoosh on every cut),
  no SFX (synth kit: pop/hit/riser/shimmer/ticks + per-world ambience), VO finished with vo_master, loudness -15.5 → -14.3 LUFS,
  bitrate 2.2 → 16.4 Mbps master, soundtrack remuxed so the render's audio guard doesn't drop level.
- Open: s3 line ("Bəs Yerdə niyə mavidir?") transcribes imperfectly — retake when Gemini TTS is responsive;
  SFX are synthesised, not library-grade; text entrances not yet timed to VO word timestamps.

## Editor QC — v4, Round 2

- delivery_qc (explainer, social, scdet 5): pass_with_warnings — -14.2 LUFS, -1.2 dBTP, 16.6 Mbps, no black/frozen frames, no dead air
- Round 1 of v4 caught a 2.5 s frozen picture at 32.2 s (comparison scene waited for the word "Marsda"); fixed with a plate push + column drift.
- Changes vs v3: ElevenLabs one-shots (whoosh, hit, pop, riser, shimmer; eleven_text_to_sound_v2) placed by measured peak;
  every text entrance, the prism split, the ×4 card and the sunset punch-in cued to narration word timestamps
  (faster-whisper medium, artifacts/vo_word_timestamps.json).
- Rubric: hook 4, story 4, rhythm 4, picture 4, typography 5, voice 3, sound 5, finishing 5
- Open: s3 narration line; ambience beds still synthesised (ElevenLabs returned 1–2 s clips, too short to loop cleanly).
