# Video Editing Skill — Talking Head, Interview, Podcast Clips

## When to Use

Apply this skill for any footage-led edit with a person speaking to camera:
talking heads, interviews, podcast/stream clips, UGC testimonials. Read
`creative/editing-craft.md` first — this playbook adds the format-specific
rules on top of it.

## Tools

| Tool | Role |
|------|------|
| `transcriber` | Word-level timestamps: filler words, dead air, false starts |
| `silence_cutter` | Automated dead-air removal (then fix by hand at word boundaries) |
| `face_tracker` | Face position for punch-in framing and caption placement |
| `auto_reframe` | 16:9 → 9:16 reframing that follows the face |
| `audio_enhance` | `vo_master` / `clean_speech` / `noise_reduce` presets for dialogue |
| `video_trimmer` | Execute cuts and speed adjustments |
| `frame_sampler` | Check frames at potential cut points (eyes closed, mid-blink) |
| `video_compose` / `hyperframes_compose` / Remotion | Assemble the final edit |
| `delivery_qc` | Objective final QC |

## 1. The paper edit first

Before touching the timeline, work from the transcript:

1. Mark the **one sentence** the clip is about. Everything else serves it.
2. Pick the **hook**: the most surprising, emotional or contrarian line in the
   whole recording — even from the middle. Open on it, then go back to
   context ("cold open").
3. Order the remaining selects into setup → tension → payoff. Reordering
   lines is normal; it's what editors do.
4. Cut everything that does not move toward the payoff, however good it is.

## 2. What to cut

1. **Filler words** ("um", "uh", "yani", "eee", "like", "you know") — cut at
   word boundaries using word timestamps; keep a few if removing them makes
   the speech sound robotic.
2. **False starts and retakes** — keep only the best delivery.
3. **Dead air** — pauses > 0.6 s in short form, > 1.2 s in long form, trimmed
   to 0.15–0.35 s. Keep longer pauses only before a punchline.
4. **Breaths** — keep most of them (attenuate by 6–10 dB rather than delete);
   removing every breath sounds machine-made.
5. **Tangents and repeated points.**

## 3. Hiding jump cuts (the professional part)

Raw jump cuts are acceptable in creator content only if they are *designed*:

- **Punch-in / punch-out**: alternate framing on every other cut — 100 % wide,
  then 115–125 % medium, then back. Centre the scale on the face (`face_tracker`).
  Never punch in twice in a row to the same size.
- **B-roll cover**: put B-roll, screen recordings, graphics or a reaction over
  the cut, with the voice continuing underneath (L-cut). Target 30–50 % B-roll
  coverage in short form, 15–30 % in long form.
- **Cut on the blink**: if a cut must stay visible, land it on a blink or a head
  movement.
- **Never** cut while the speaker's eyes are closed or the mouth is mid-word
  on the outgoing frame (`frame_sampler`).

## 4. Captions for talking heads

- Burned-in, 2–5 words per page, timed to word timestamps (`subtitle-sync`).
- Emphasis words get colour or scale on the spoken syllable; one accent
  colour only.
- Position in the lower-middle third, clear of the face and of platform UI.
- Correct the transcript first: names, brands and Azerbaijani/Turkish
  characters (ə, ğ, ı, ö, ü, ş, ç) must be exact.

## 5. Sound for dialogue

1. Clean: `audio_enhance` `noise_reduce` only if there is audible noise, then
   `vo_master` (HPF 80 Hz, mud cut 250 Hz, presence 3–5 kHz, de-ess, gentle
   compression, loudness).
2. Room tone under every cut so the background doesn't "switch off".
3. Music: low-energy bed, ducked 15–18 dB under speech; music swells only in
   the gaps (hook, transitions, ending).
4. SFX: soft whoosh on punch-ins that coincide with section changes, pop/click
   on caption emphasis — subtle, ≥ 10 dB under voice.

## 6. Colour and picture

- Correct exposure and white balance first; skin tones on the skin-tone line
  (`skills/core/color-grading.md`, Skin Tone Protection).
- Match every clip to the hero shot before applying a look.
- Light sharpening and denoise only if the source needs it.

## 7. Pacing by length

| Length | Pace |
|---|---|
| < 60 s | Aggressive: a cut, punch-in or insert every 2–4 s; dead air ≤ 0.3 s |
| 1–10 min | Balanced: a visual change every 5–10 s; keep breathing pauses |
| > 10 min | Let it breathe; chapter cards, B-roll at topic shifts, cut only obvious problems |

## Edit Decision Structure

The `edit_decisions` artifact should include:

- **cuts**: ordered segments (source, in/out, speed), each with `reason`
  (hook, setup, payoff, reaction, broll_cover)
- **framing**: per-cut scale/position for punch-ins
- **overlays**: B-roll, graphics, lower thirds with in/out times
- **subtitles**: style, source file, emphasis words
- **music**: asset, ducking, in/out points on phrase boundaries
- **sfx**: cue list (time, file, gain)
- **transitions**: type and timing (default straight cut / J / L)

## Quality Checklist

- [ ] Opens on the hook line, not on a greeting
- [ ] No unintended visible jump cut (each is punched, covered or on a blink)
- [ ] Cuts at word boundaries; no clicks or pops (2–5 ms fades on every audio edit)
- [ ] Room tone continuous; no silence holes
- [ ] Captions exact, timed, inside safe zones, not over the face
- [ ] Voice intelligible over music everywhere; delivered at −14 LUFS / ≤ −1 dBTP
- [ ] `delivery_qc` has no `fail`; every `warn` is fixed or justified
