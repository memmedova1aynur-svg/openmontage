---
name: ig-carousel
description: >-
  Build an Instagram carousel - the cover that earns the swipe, slide-by-slide
  copy, and the 1080x1350 files to upload. Use when the user says "carousel",
  "slides", "swipe post", "turn this into a carousel", or has a list-shaped or
  step-shaped idea that would die as a single image.
---

# ig-carousel

## Which client

This project runs several clients' Instagram accounts. Every per-account file
lives in `instagram-clients/<client>/` at the project root, where `<client>` is
the client's folder name (lowercase, hyphens). These paths are relative to
the project root, so when a script in this folder takes an output path, pass
it the absolute one.

Client folders are private and are NOT committed to this repo (it is a public
fork; see `.gitignore`). The copy that persists is the `instagram-clients`
folder in the user's Google Drive, one subfolder per client. If
`instagram-clients/<client>/` is missing locally, download it from Drive
first. After you create or change a client file, upload it back to the same
Drive subfolder, updating the existing file rather than adding a duplicate.
On Drive each file is a Google Doc, written in Azerbaijani so the agency can
read it, and named in Azerbaijani: `voice.md` is "Səs profili", `audit.md` is
"Analiz", `profile-rewrite.md` is "Profil yenidən yazılışı". Upload markdown
with conversion on (not raw `.md`, which Drive cannot preview), and replace
emoji outside the Basic Multilingual Plane (e.g. U+1F447) with plain symbols
or words: the converter corrupts them.

Draft in the chat first. Scripts, captions, plans and other drafts are
discussed and revised in the conversation; only what the user approves is saved
to the client's Drive folder. Never upload a draft the user has not approved.
This includes the voice profile: keep it updated locally as facts change, but
upload it to Drive only when the user explicitly says to.

Agency rules, for every client, overriding anything below that conflicts:
- No agitation. Never show the expert's struggles, fears or private life.
  Present them professionally: decisions, knowledge, growth.
- One video, one topic. No jumping between events or subjects in one reel.
- Every video stands alone. No "part 1" or cliffhangers unless the user asks
  for a series.
- Always write the full spoken text of every video: conversational
  Azerbaijani in short lines, no bookish phrasing. Do not label scripts
  "prompter" or "directions"; the team decides on set whether to read it from
  the teleprompter, say it from memory or speak freely. Experts shoot 5-10
  videos in one 1-2 hour session. Facts only the expert knows (their story,
  program details, their own methods) go in as [square-bracket blanks]; never
  invent them. Methodology advice is phrased as advice ("do X"), not as the
  expert's personal habit, unless the expert has confirmed it. Documents sent
  to the expert hold only what they say; montage plans go to the team
  separately.
- Follow the positioning section of the client's voice profile above all.
- Carousels are 5-6 slides at most. Vary the cover between consecutive
  carousels (renderer variants light / dark / split, different icons) while
  staying inside the client's brand colours and fonts.

1. Work out which client this is for. If the user has not named one and the
   conversation has not already settled it, list the folders in
   `instagram-clients/` and ask. Never guess, and never carry one client's
   voice, numbers or plans into another client's work.
2. If the client has no folder yet, copy `instagram-clients/_template/` to
   `instagram-clients/<client>/` and fill in what you know.
3. Read `instagram-clients/<client>/voice.md` before writing anything, and
   write in the content language it names.

Carousels are the highest-dwell format on the grid, because a swipe is an
interaction and a scroll is not. They also get a second chance: Instagram can
show a carousel again starting from a later slide to someone who did not engage
the first time, so slide two has to stand on its own as well.

The format rewards one idea broken into steps. It punishes a caption cut into
pieces.

## When to use it instead of a Reel

Use a carousel when the idea has **sequence and needs to be re-read**: steps, a
framework with parts, a before and after, a list worth screenshotting. Use a
Reel when the idea has motion, a face, or a payoff that has to be seen
happening.

If the idea is one claim, it is neither. Hand it to `/ig-reel` and say so.

## Structure

6 to 10 slides. The cap is 20 and 20 is almost always a book nobody finishes.
Under 5 and the swipe never starts.

```
1         COVER     the hook. 6 words or fewer, at a size that is legible in
                    the grid at thumbnail. One line of promise under it.
2         THE STAKE why this matters, in one sentence. This slide is also a
                    second cover, so it cannot be setup.
3 to N    ONE IDEA PER SLIDE. A headline of 3 to 7 words, at most 25 words
                    under it. If a slide needs a paragraph, it is two slides.
N+1       RECAP     the whole thing as a list. This is the screenshot slide.
LAST      CTA       one action. Save, comment a keyword, or follow. One.
```

## Slide copy rules

- **The cover is 80% of the result.** Six words. Big. Nothing on the deck saves
  a cover nobody swipes.
- **Design for the grid crop.** The profile grid crops to a portrait rectangle
  that is taller than it is wide, and the exact ratio has moved more than once.
  Build at 1080x1350 and keep the cover text well inside the middle, clear of
  the outer 120 pixels on every side, and the crop stops mattering.
- **Number the slides** (3/8). Completion goes up when people can see the end.
- **No slide is a paragraph.** If it cannot be said in 25 words, split it.
- **The recap slide is the one people screenshot and send.** Sends are the
  strongest signal you can earn. Make it standalone and readable with no
  context.
- **The handle on every slide**, small, bottom corner. Screenshots travel
  without you.
- **Alt text on the cover at minimum.** It is read by screen readers and by
  Instagram.

## Building the files

Use the renderer in this folder. It typesets every slide from JSON with the
client's brand, so there is no generative AI involved (no AI-content label on
Instagram) and Azerbaijani letters always come out right.

1. Write `instagram-clients/<client>/carousels/<yyyy-mm>-<slug>/slides.json`:

```json
{ "slides": [
  { "type": "cover", "variant": "light | dark | split",
    "icon": "question | levels | game | star | chat | bulb | check",
    "label": "SPEAKING SKILLS", "headline": "...",
    "highlight": "words inside the headline to mark", "sub": "...",
    "photo": "optional image path, relative to slides.json" },
  { "type": "statement", "text": "..." },
  { "type": "point", "n": "01", "headline": "...", "body": "up to 25 words" },
  { "type": "recap", "headline": "Xülasə", "items": ["...", "..."] },
  { "type": "cta", "headline": "Saxlayın", "body": "..." },
  { "type": "photo", "photo": "img.jpg", "hint": "...", "headline": "...", "body": "..." },
  { "type": "overlay", "photo": "img.jpg", "hint": "...", "headline": "...", "body": "..." },
  { "type": "level", "badge": "B1", "items": ["question", "..."], "note": "..." },
  { "type": "compare", "label_bad": "Belə yox", "bad": "...", "label_good": "Belə", "good": "...", "note": "..." }
] }
```

2. Render, from the project root:

```bash
node .claude/skills/ig-carousel/render.js \
  instagram-clients/<client>/carousels/<dir>/slides.json \
  instagram-clients/<client>/brand.json \
  instagram-clients/<client>/carousels/<dir>/
```

Themes: set `"theme"` at the top of slides.json to `classic` (default),
`editorial` (serif headlines, italic gold accents, hairlines), `night` (every
slide navy) or `cards` (content on a paper card over the soft blue). Rotate
themes so consecutive carousels on the grid do not look alike.

The `accent` theme marks highlighted words in gold text instead of a box.
Covers also take `"chain": [icon, ...]` (a vertical row of icon circles joined
by a gold line) and `"pill": "Ətraflı bax"` (a call-to-action pill). A brand
with `"signature": {"name", "sub"}` gets a two-line signature in the footer.

Illustrations: add `"art": ["hourglass", "dice"]` to any slide to draw flat
line illustrations in the brand palette in the lower part of the slide (first
item large, the rest smaller). Pick drawings that match the slide's idea; give
most body slides one or two. Available: hourglass, dice, target, cards, chat,
pawn, notepad, pencil, stopwatch, book, music, blocks, star, bulb, laptop,
board, puzzle, trophy, magnifier, headphones (see `illustrations.js`; add new
ones there in the same style rather than using AI images). The renderer fails
if text runs into the illustration; shorten the text.

Photos: the expert's own shots or frames from their videos come first; free
stock (Unsplash, Pexels) only if the user supplies the files. Avoid AI-generated
images: Instagram may label them. Without `photo`, a placeholder showing `hint`
is drawn so the layout can be approved first.

It writes `01.png`, `02.png`, ... at 1080x1350 and exits non-zero if any text
runs into the footer; shorten the copy and render again. Look at the cover and
at least one body slide before showing them. The client's colours, name line
and handle live in `instagram-clients/<client>/brand.json` (copy it from
`_template/` for a new client). Fonts are bundled in `fonts/` (Montserrat,
SIL Open Font License).

3. Show the PNGs to the user. Upload them to the client's Drive folder only
   after approval.

## Output

The slide-by-slide copy first, as a numbered list the user can read in ten
seconds and edit before anything is rendered. Then the **caption**, which for a
carousel is Job B in `/ig-caption`: the caption is doing work here, because the
cover has already used its six words.

Run both through `/ig-human`. Build the files only after the user approves the
copy.

```
CAROUSEL  ·  8 slides

1  COVER   THE $18,000 CLAUSE
           One line I now put in every contract.
2  STAKE   I approved the work. They asked for the money back nine days later.
3          WHAT IT SAYS
           Payment on delivery, not on approval.
...
7  RECAP   All four lines, in order.
8  CTA     Comment CONTRACT and I will send the full clause.

Caption: Job B, hook in line 1, one ask, 3 tags.
```

Nothing is uploaded. The user posts it.
