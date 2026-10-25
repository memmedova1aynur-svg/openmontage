---
name: ig-week
description: >-
  Build a client's weekly package for one shoot - 6-8 reel scripts in shoot
  order with montage plans, cover titles and captions, an optional carousel
  rendered to PNG, a 7-day posting schedule and story ideas. Use when the user
  says "weekly package", "həftəlik paket", "this week's shoot", "next shoot",
  or names a client and a week.
---

# ig-week

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

1. Work out which client this is for. If the user has not named one and the
   conversation has not already settled it, list the folders in
   `instagram-clients/` and ask. Never guess, and never carry one client's
   voice, numbers or plans into another client's work.
2. If the client has no folder yet, copy `instagram-clients/_template/` to
   `instagram-clients/<client>/` and fill in what you know.
3. Read `instagram-clients/<client>/voice.md` before writing anything, and
   write in the content language it names.

One package = one shoot. The expert reads it on the teleprompter in one
1-2 hour session; the team edits, makes covers, schedules in Instagram. Make
every part copy-ready, because nobody has time to rewrite it.

## Inputs

- The month plan (`/ig-month`). Take the next unused topics from it. If there
  is no month plan, say so and offer to make one first.
- The voice profile and agency rules.
- Anything the user adds for this week (an event, a date, a new group).

## The package

1. **Shoot list.** 6-8 videos in the order they will be filmed, grouped so
   they can be shot with one outfit and one setup. Mark 1-2 as spare.
2. **Per video:**
   - On-screen title (2-5 words) - also the cover headline.
   - Script. `prompter`: the full text in short spoken lines, 20-45 seconds,
     the hook in the first line, one idea, a single soft ask at the end.
     `directions`: talking points, example sentences, blanks.
   - Montage plan: which footage goes where, the 1-2 on-screen cards,
     subtitles on.
   - Caption, copy-ready (follow `/ig-caption`).
3. **Carousel** if the month plan has one this week: slide copy first; after
   approval, render with `ig-carousel/render.js` and show the PNGs.
4. **Schedule.** 7 days, one reel a day, carousels in between, with times.
5. **Story ideas.** 3-4 for the expert to post themselves (a poll, a question
   box, a behind-the-scenes moment from the shoot).

## Rules

- Never invent facts, numbers or results about the expert. Ask first.
- Read every prompter script as if saying it aloud: no line the expert would
  stumble on, no word they would not use.
- Draft in the chat. On approval, upload to the client's Drive folder as one
  Google Doc named "Həftə <n> — <date range>" plus the carousel PNGs, and log
  the week's titles to `log.md`.
