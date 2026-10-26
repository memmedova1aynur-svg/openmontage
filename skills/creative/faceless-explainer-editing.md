# Faceless Explainer Editing — Animated, Motion-Graphics, Narrated Shorts

## When to Use

Narrated videos without a presenter: animated explainers, science/history
shorts, motion-graphics, data stories, faceless YouTube/Reels channels
(`animated-explainer`, `animation`, `documentary-montage`, HyperFrames,
Remotion, Manim). Read `creative/editing-craft.md` first.

The trap of this format is the **slideshow**: one image per sentence, a fade,
the next image. The fix is to treat narration, picture and sound as one
choreography.

## 1. Script → beat sheet → picture

1. Write the narration first, then split it into **beats** (one idea each,
   1.5–4 s of speech).
2. For every beat decide: what does the viewer **see change** at the key word?
   If nothing changes, the beat needs a new visual or should merge.
3. Generate VO **before** final animation timing. Time the animation to the
   real VO word timestamps (`transcriber` on the TTS output), never to guessed
   durations.

## 2. Visual grammar

- **One focal point per frame.** The eye should know where to look within
  0.3 s; use scale, contrast, motion and colour to lead it.
- **Build, don't present.** Diagrams assemble element by element in sync with
  the words; lists reveal one item per spoken item.
- **Continuity between scenes**: carry an element across the cut (the planet
  becomes the dot on the chart; the beam continues into the next shot) —
  match cuts instead of fades.
- **Depth**: foreground/midground/background layers with parallax; subtle
  particles, light, grain. Flat single-layer frames look cheap.
- **Real plates beat clip art**: photographic, generated or physically
  rendered backgrounds with graphics on top. Flat CSS gradients and circles
  read as placeholder art.
- Keep a consistent **style bible**: palette (≤ 5 colours + one accent),
  type pair, line weight, corner radius, motion easing. Write it into the
  playbook before producing assets.

## 3. Motion

- Every scene has at least one primary motion (camera push, element build) and
  one secondary motion (particles, drift, light).
- Entrances 0.35–0.6 s with ease-out; exits faster than entrances (0.2–0.35 s).
- Stagger related elements 40–120 ms; never animate everything at once.
- Overshoot (back.out) only for playful tone and only on key elements.
- Text kinetic emphasis on the stressed word, not on the whole line.

## 4. Narration and sound

- Narration directed per beat (`creative/vo-production.md`): pauses after
  setups, slower on the key line, energy up on the payoff.
- Music under narration: −16 to −20 dB relative, sidechain ducked, swells in
  the gaps and on the payoff.
- SFX layer is non-negotiable for animation: whoosh for moves, pop/tick for
  element entrances, riser into reveals, low hit on big statements, subtle
  ambience per world (space hum, wind, room).
- Leave 0.2–0.4 s of breathing room after major statements before the next
  line starts.

## 5. Pacing

| Platform | Visual change | Typical length |
|---|---|---|
| Reels / Shorts / TikTok | every 1.5–3 s | 30–60 s |
| YouTube explainer | every 3–6 s | 3–12 min |

Hook in the first second with the most striking visual and a question or
contradiction; payoff ≥ 70 % through; end with a loop-back or a one-line
takeaway, not a long outro.

## 6. Scene transitions

Default: straight cut on the narration's sentence boundary, with the next
scene's first motion already in progress (enter mid-motion). Use a designed
transition (match cut, morph, wipe driven by an on-screen element) at section
breaks. Never fade each scene in from black — scenes must overlap so no
background colour shows through.

## Quality Checklist

- [ ] Every beat has a visible change on its key word
- [ ] No still frame without motion for > 3 s (short form)
- [ ] Animation timed to real VO word timestamps
- [ ] Style bible respected across scenes
- [ ] SFX on moves/entrances/reveals; music ducked under voice
- [ ] No black flashes between scenes; no stray fades
- [ ] `delivery_qc` (format `explainer` or `short_form`) has no `fail`
