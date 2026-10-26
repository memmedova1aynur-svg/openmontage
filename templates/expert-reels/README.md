# Expert Reels template

Edits a phone-shot, single-speaker vertical video (an expert talking to camera)
into a finished Instagram Reel. The output has:

- Word-by-word Azerbaijani captions in Montserrat. A caption page never runs
  past a sentence or a comma, so each sentence starts on a fresh line.
- Rhythmic zooms: hard cuts, smooth pushes, and punch-ins with a micro-shake.
- Keyword pills.
- Animated cutaways with the speaker in a corner circle.
- An Instagram comment-box CTA.
- Synthesized SFX: whoosh, pop, hit, tick and ding.
- The original audio (including any music already in the footage), normalized
  to -16 LUFS.
- Two-pass encode to about 26 MB for 60 s, under Claude's 30 MB upload limit.

> **AZ qısa:** Bu şablon mütəxəssis videolarını eyni peşəkar səviyyədə, amma hər
> dəfə fərqli görünüşlə montaj etmək üçündür. Hər mütəxəssisin öz rəng
> profili (`experts/<id>.json`) var. Hər video üçün ara kadrlar mövzuya görə
> seçilir, üslub variantları isə əvvəlki videolardan fərqli götürülür.

Reference build: the "6 aylıq karyera xəritəsi" consultation Reel (Oct 2026).

## Pipeline

This runs the `talking-head` pipeline (see `skills/pipelines/talking-head/`).
The `expert-reels-director` skill says how this template plugs into it.

```
1. Get the footage (> 30 MB: Google Drive link shared as "Anyone with the link").
2. Transcribe:  transcriber tool, model_size=large-v3, language=az
3. Correct the transcript by hand, show it to the user, get approval.
3b. Retakes: when a sentence was said more than once, keep the best complete take:
                python templates/expert-reels/scripts/cut_takes.py <src> <words.json> keep.json base.mp4 words_cut.json
                (keep.json = [[start, end], ...] in source seconds, cut in the pauses)
                (the last range is held 1 s past its end so the final sentence is never clipped;
                 build_edit.py reads the video length from the footage)
4. Align:       python templates/expert-reels/scripts/align_words.py \
                  projects/<id>/artifacts/<x>_transcript.json corrected.txt \
                  projects/<id>/artifacts/corrected_word_segments.json
5. Workspace:   templates/expert-reels/scripts/setup_workspace.sh <id> <source-video>
6. Spec:        write projects/<id>/spec.json (format below)
7. Build:       python templates/expert-reels/scripts/build_edit.py projects/<id>/spec.json projects/<id>/remotion
8. Preview:     STILL=<frame> templates/expert-reels/scripts/render.sh <id>   (look at every cutaway)
9. Render:      templates/expert-reels/scripts/render.sh <id> final
10. Log the style + scenes used in experts/<expert>.json "history".
```

## Expert profile (`experts/<id>.json`)

Copy `experts/_example.json`. Take the colours from the expert's own Instagram:
grid, highlight covers, logo. Don't take them from the footage. Ask the user for
a screenshot of the profile if no brand colours are given.

| key | role |
|---|---|
| `primary`, `primaryDeep` | card and backdrop tones (the expert's dark brand colour) |
| `accent`, `accentSoft` | active caption word, labels, bars, tiles |
| `text`, `onAccent` | text on `primary` / on `accent` |
| `emphasis` (optional) | colour of `**highlighted**` words; set it when `accent` is close to `text` |
| `light` (optional) | pale theme: captions over cutaways turn dark instead of white + stroke |
| `style` | the expert's default style picks (overridable per video) |
| `history` | the style + scenes of every delivered video, newest last |

Contrast check: `accent` on `primary`, and `onAccent` on `accent`, need at
least 4.5:1. If the brand accent is light (pastel pink, mint), use it for
accents and keep captions white with stroke.

## Spec (`projects/<id>/spec.json`)

See `examples/sample.spec.json`. All times are seconds in the source, read from
the aligned word timings. Wrap text in `**double stars**` to draw it in the
accent colour.

- `zoom`: `[t, scale, kind]`. `cut` = instant, `push` = smooth, `punch` =
  fast with a shake and a hit SFX. Put cuts and pushes on sentence and clause
  starts. Save punches for 2-3 key lines.
- `overlays`: keyword pills (`hook` | `pill` | `cta`). `parts` = `[[text, highlight]]`.
  `pop` + `pos` (`t` | `tl` | `tr` | `l` | `r`) is a short emphasised word that bounces in around the
  speaker. Use it for talking-only videos (no cutaways): 1-3 words, 1.2-2.5 s, varied sides.
  Pills that overlap a cutaway are dropped automatically.
- `cutaways`:
  - `pip`: the speaker shrinks into the corner. `panels` play in order, each
    with `kind`, `at` and `props`.
  - `full`: the scene replaces the speaker for a few seconds (voice continues). Keep these to 3-5 s and
    2-3 per video when the user wants a calmer edit without the corner frame.
  - `comment`: the speaker stays full screen and an IG comment bar types
    `keyword`.
- `pip`: `focus` is the head-and-shoulders point of the speaker in the
  1080x1920 frame. Measure it on a gridded frame so the circle holds head and
  shoulders with no empty background. `radius` is about 210 and `scale` = radius / local radius.
- `style`: per-video overrides (see Variety).
- `video`: footage file in `public/` (default `base.mp4`). For a softly blurred background run
  `python templates/expert-reels/scripts/blur_background.py public/base.mp4 public/base_blur.mp4`
  (MODNet portrait matting, Apache-2.0) and set `"video": "base_blur.mp4"`.
- `sfx_level`: `"minimal"` for calm edits. Use it when the user asks for something simple; it drops zoom pops and softens the rest.

### Scene library (`src/scenes/index.tsx`)

| kind | use when the speaker... | props |
|---|---|---|
| `timeline` | gives a plan, steps, months, a process | `label, title, steps ["AY\|1",...], times[], footer, footerAt` |
| `phone` | talks about Instagram, a page, an app, content | `label, title, checks[], times[], tiles` |
| `checklist` | lists what you get or what to do | `label, title, items[], times[]` |
| `chat` | mentions messages, DMs, scripts, client talk | `label, title, messages [{from: me\|them, text}], times[]` |
| `questions` | opens with the viewer's doubts or questions | `questions[], times[]` |
| `stat` | says a number worth feeling | `label, value, prefix, suffix, caption` |
| `comment` (cutaway kind) | the CTA is "comment X" | `hint, keyword, type_start, type_end, send` |

`times[]` puts each item on the exact word that names it. Always set it;
staggered defaults are only a fallback.

## Variety: no two videos the same

The template is shared. The look must not repeat. For every new video:

0. **Pacing.** Don't leave the speaker talking straight to camera for more than ~6 s without a change (insert, card or zoom). Long static stretches lose viewers.
1. **Scenes come from the topic.** Read the approved script and pick 2-4
   cutaways whose content the speaker says out loud. Don't add a scene for
   decoration, and don't invent numbers or claims that aren't in the script.
2. **Rotate the style axes.** Compare with the expert's `history` and change at
   least two of these from the previous video:
   - `captions`: stroke / box / chip
   - `pills`: top-card / side-tag
   - `backdrop`: dots / grid / orbs / diagonal
   - `pipShape`: circle / rounded
   - `pipCorner`: br / bl
   - `pops`: dark / light (keyword pop cards)
   Same set and outfit as the previous video? Change `captions` and `pops` at least, or the two read as one video.
3. **Vary the structure.** Don't open with the same device twice in a row (a
   pill hook, then a questions cutaway, then a stat). Move where the first
   cutaway lands.
4. **Different experts have different palettes.** Never reuse another
   expert's theme.
5. **New scene types are welcome.** If a topic needs a visual the library
   lacks (before/after, map, price card), add it to `src/scenes/` and to the
   table above.

## Notes

- Fonts: Montserrat (SIL OFL, `public/fonts/Montserrat-OFL.txt`), latin and
  latin-ext subsets. latin-ext covers ə ğ ı ş ç ö ü.
- Caption zone: the bottom of the caption block is at y=1490, above Instagram's
  username/caption UI. Pills and cutaway titles start at y>=300, below the top
  bar.
- Remotion can't download its headless shell behind the sandbox proxy.
  `render.sh` uses the pre-installed Playwright Chromium when it is present.
- SFX are generated by `build_edit.py`, so they are royalty-free and need no
  network.
