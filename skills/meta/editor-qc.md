# Editor QC — The Senior Editor's Final Pass

## When to Use

**Mandatory before presenting any final render to the user or publishing it**,
for every pipeline and format. It runs after `reviewer.md`'s compose-stage
review and before the publish checkpoint. A render that has not passed this
gate is a draft, and must be presented as one.

## Step 1 — Objective QC (`delivery_qc`)

```python
from tools.analysis.delivery_qc import DeliveryQC
DeliveryQC().execute({
    "input_path": "projects/<p>/renders/final.mp4",
    "loudness_profile": "social",       # social | youtube | podcast | broadcast | cinema_web
    "format": "short_form",             # short_form | ad | explainer | talking_head | documentary | cinematic
    "expected": {"width": 1080, "height": 1920, "fps": 30},
    "intentional_holds": [[45.5, 48.0]] # end card, designed freeze frames, intended silence
})
```

- Any `fail` → fix and re-render. No exceptions.
- Each `warn` → fix, or write a one-line justification in the decision log
  (e.g. "longest shot 8 s at 23 s: diagram builds continuously").
- Report the measured LUFS, true peak, cuts/min and average shot length to
  the user alongside the video.

## Step 2 — Watch it like a viewer (frame review)

Extract frames with `visual_qa` (`review`) at: 0.5 s, every cut ± 3 frames,
every text entrance, the payoff, the last 2 s. Look at them; don't assume.

Check:
- First frame is already interesting (it's the thumbnail in many feeds)
- No black/blank/half-loaded frames at cuts; no layout jumps
- Text: spelled correctly (diacritics!), readable size, inside safe zones,
  never over faces or the product
- Visual hierarchy: one focal point per frame

## Step 3 — Score the craft (rubric)

Score 1–5 each. Ship only if **every** dimension ≥ 4 (≥ 3 for a declared
draft/prototype).

| Dimension | 5 looks like |
|---|---|
| **Hook** | Strongest image/line in the first 1–3 s; no warm-up |
| **Story & clarity** | One message, clear setup → payoff; nothing redundant |
| **Rhythm** | Shot length varies with intent; cuts land on words/beats/actions |
| **Picture** | Consistent grade, real depth/texture, motion on every frame |
| **Typography** | Readable, timed to speech, consistent system, safe zones |
| **Voice** | Directed performance, correct pronunciation, no TTS tells |
| **Sound design** | Music edited to picture, ducked; SFX on motion; no dead air |
| **Finishing** | Loudness/peak on spec, no glitches, high-bitrate master |

Use `creative/editing-craft.md` and the format playbook
(`video-editing.md`, `ad-editing.md`, `faceless-explainer-editing.md`,
`vo-production.md`) as the reference for each score.

## Step 4 — Fix list and re-run

Write the fixes as concrete edits ("move cut at 12.40 → 12.26 onto 'mavi'",
"add whoosh at 17.0", "overlap s5/s6 by 0.3 s to remove black flash"), apply
them, re-render, and repeat Steps 1–3. Two rounds is normal for professional
work.

## Step 5 — Record

Append to the project's review record:

```markdown
## Editor QC — Round N
- delivery_qc: verdict, LUFS, TP, cuts/min, ASL
- Rubric: hook 4, story 5, rhythm 4, picture 4, type 5, voice 4, sound 4, finishing 5
- Fixed: …
- Justified warnings: …
```

When presenting to the user, state the scores honestly, including anything
below 5 and what would raise it.
