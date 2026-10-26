# Editing Craft — How a Professional Editor Thinks

## When to Use

Read this before the `edit`, `assembly` or `compose` stage of **every** pipeline,
whatever the format. It is the shared grammar; the format playbooks build on it:

| Format | Playbook |
|---|---|
| Talking head, interview, podcast clip | `creative/video-editing.md` |
| Ads, promos, UGC-style commercials | `creative/ad-editing.md` |
| Faceless explainers, motion-graphics, animated shorts | `creative/faceless-explainer-editing.md` |
| Narration / TTS voice | `creative/vo-production.md` |
| Final pass before delivery | `meta/editor-qc.md` |

Amateur edits fail in predictable ways: every shot the same length, cuts that
land on nothing, music that ignores the picture, a voice that reads instead of
talks, and no idea what the viewer should feel at second 3, 15 and 40. Each
rule below exists to prevent one of those.

## 1. Every cut needs a reason

A cut is justified by at least one of: **new information**, **action**
(movement starts/continues), **emphasis** (a word, a beat), **reaction**, or
**time** (compressing what doesn't matter). If you cannot name the reason,
the cut is decoration — remove it or move it.

- **Cut on action.** Cut while something moves (a gesture, a camera move, an
  element entering). Motion hides the cut; a cut between two static frames is
  felt.
- **Cut on the beat, not every beat.** Land major cuts on downbeats or
  phrase starts; land minor cuts on off-beats or let them float. Cutting on
  every beat is a music video, not an edit.
- **Cut on the word.** Visual changes land on the stressed syllable of the
  word they illustrate (± 2 frames), not at the start of the sentence.
- **Lead with sound.** Use J-cuts (next audio starts 6–15 frames before the
  picture) to pull the viewer forward and L-cuts (audio carries over) to let a
  thought land. Pure straight cuts on every edit feel like a slideshow.

## 2. Rhythm is variation

Shot length should *breathe*: a run of short shots, then one held shot that
lets the idea land, then accelerate again. Uniform shot length is the single
most common "AI-made" tell.

| Format | Typical average shot | Never hold a static frame longer than |
|---|---|---|
| Short-form / Reels | 1.5–3 s | 4–6 s |
| Ad (15–30 s) | 0.8–2.5 s | 3–5 s |
| Explainer | 2.5–5 s | 8 s (unless the frame itself animates) |
| Talking head | 4–10 s (with punch-ins) | 12–20 s |
| Documentary / cinematic | 4–12 s | as long as it earns |

"Static" means nothing changes. A held shot with a slow push, a counter
ticking, or a diagram building is not static. `delivery_qc` reports average
and longest shot so you can check this objectively.

**Pattern interrupts**: in short-form, change *something* every 2–4 s — framing
(punch-in), a graphic, a sound hit, a caption style beat, a B-roll insert.

## 3. Structure the attention curve

Plan what the viewer feels at each moment before cutting:

1. **Hook (0–3 s)**: the most surprising image/claim first. No logos, no
   "hi guys", no slow fade from black. Start on motion and sound.
2. **Promise (3–8 s)**: tell them what they will get by staying.
3. **Escalation**: each section raises the stakes or the curiosity; put the
   second-best moment at ~60 % of the runtime to catch drop-off.
4. **Payoff**: deliver the promise clearly, with the strongest visual.
5. **Button / CTA**: one short beat. End *on* the payoff energy; do not fade
   out slowly over a dead card.

## 4. Transitions: the straight cut is the default

- 90 % of transitions should be straight cuts or J/L cuts.
- **Match cuts** (shape, motion, colour or sound continuing across the cut)
  are the professional "wow" transition — plan them in the scene plan.
- **Whip/zoom/blur transitions**: max one per 10–15 s and only between
  sections, always with a whoosh SFX synced to the peak.
- **Dissolves** mean time passing or a mood shift — not "I didn't know how to
  cut".
- **Dip to black** only at a true chapter break. Never let a scene fade in
  from black mid-programme by accident (a 2–4 frame black flash between
  scenes reads as a glitch — `delivery_qc` flags it).

## 5. Motion and camera

- Every still or render plate gets motion: slow push (100 → 106–110 % over
  the shot), drift, or parallax layers. Alternate direction between
  consecutive shots so the movement doesn't feel like a screensaver.
- Ease everything (`power2/power3` or custom curves); linear motion only for
  constant drifts.
- Keep motion directions consistent within a sequence (screen direction): if
  the "journey" goes left → right, keep it that way.
- Punch-ins on a talking head: 100 % → 115–125 % on emphasis, back on the
  next thought. Never two punch-ins of the same size back-to-back.

## 6. Sound is half the picture

Read `creative/sound-design.md` and `creative/vo-production.md`. Minimum bar:

- Voice is king: always intelligible, music ducked under it (-12 to -18 dB
  relative), sidechain not a static volume drop.
- **Every visual event that moves fast gets a sound**: whoosh on transitions,
  soft hit/click on text slam, riser into a reveal, sub-drop on the payoff.
  Keep SFX 6–12 dB under the voice.
- **Never true silence** inside the programme — use room tone, ambience or
  music tail. Intentional silence is a choice and is short (≤ 1 s) before a
  big line.
- Cut music on phrase boundaries; when shortening a track, cut bar-to-bar and
  crossfade 50–150 ms. End on the track's real ending (or a hit), not a fade
  in the middle of a phrase.
- Deliver to the platform loudness (social/YouTube −14 LUFS, true peak ≤ −1
  dBTP).

## 7. Text on screen

Follow `creative/typography.md`. Editing-specific rules:

- On screen ≥ 0.25 s per word, minimum 1.2 s for any line.
- Text enters on the word that is spoken (karaoke-style emphasis for short
  form), leaves before it becomes stale.
- Max 2 type sizes and 2 weights per frame; one accent colour.
- Keep inside platform safe zones (9:16: top 220 px and bottom 420 px are UI;
  right 140 px has buttons).

## 8. Finishing

- Consistent grade across shots (`skills/core/color-grading.md`), then a
  final look: subtle contrast curve, vignette, fine grain unify generated and
  rendered sources.
- Export a high-bitrate master (H.264 CRF 16–18 or 12–20 Mbps for 1080×1920,
  yuv420p, AAC 320 kbps 48 kHz). Platforms re-encode; a starved upload looks
  worse twice.
- Run `delivery_qc` and the `meta/editor-qc.md` rubric. Nothing ships with a
  `fail`.

## Anti-patterns (instant amateur tells)

- Same shot length and same transition for the whole video
- Text that appears all at once, then sits there
- Music at constant volume under the voice, or ending mid-phrase
- Cuts that land between words or a few frames after the beat
- Fade from/to black between every scene
- Stock zoom/whip transitions without sound
- A static still for more than 4 s in short form
- Narration that never pauses, or pauses at the same length every time
