# Expert Reels Director — Talking Head Pipeline

## When to Use

The user sends a vertical phone video of an expert (coach, trainer, consultant)
talking to camera and wants an Instagram Reel. Typical extras they ask for:
captions, dynamic zooms, animated inserts, sound effects. Use
`templates/expert-reels/`; its `README.md` is the operating manual.

This skill does not replace the talking-head stage directors. It replaces the
generic overlay and compose path for the scene_plan, assets, edit and compose
stages with the template's spec → `build_edit.py` → `render.sh` flow.

## Binding Rules

1. **Transcript approval first.** Transcribe with `large-v3` and `language=az`.
   Hand-correct the transcript and show the full text to the user. List every
   word you were unsure of, then wait for approval. The approved text drives
   the captions through `align_words.py`.
2. **Expert profile.** Find or create `templates/expert-reels/experts/<id>.json`
   with the expert's own Instagram colours. Ask for a profile screenshot or
   brand colours if you don't have them. Never borrow another expert's theme.
3. **Topic-driven cutaways.** Pick 2-4 scenes from the library that match what
   is actually said. Sync items with `times[]` to the exact words.
4. **No repeats.** Read the expert's `history` and change at least two style
   axes from the previous video (README → Variety). After delivery, append the
   video's style and scenes to `history`.
5. **Keep the footage's audio.** Experts often add music before sending. Check
   the pauses for a music bed before you propose adding music. The user edits
   in CapCut, so deliver without added music unless they ask for it.
6. **Preview before the full render.** Render a still of every cutaway and of a
   caption page, and look at them. Check contrast, overlaps with the speaker
   circle, and whether the circle holds head and shoulders with no empty
   background.
7. **Delivery.** `render.sh` writes `projects/<id>/renders/<name>.mp4`
   (< 30 MB). Send it with SendUserFile. Offer an Instagram caption via the
   `ig-caption` skill.

## Gate Reminder

The transcript gate (rule 1) is binding. Later gates follow the user's stated
autonomy. If they said "finish it and send it", render and deliver, then take
feedback as a revision round.
