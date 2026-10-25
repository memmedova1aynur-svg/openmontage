---
name: ig-month
description: >-
  Plan a client's month on Instagram - about 30 reel topics plus carousel
  topics, spread across the month's 4 shoots and tied to what the client is
  selling that month. Use when the user says "month plan", "ay planı",
  "next month's topics", "plan November", or starts a new month for a client.
---

# ig-month

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
- Script format depends on the video. Experts shoot with a teleprompter, 5-10
  videos in one 1-2 hour session. Methodology and educational videos get a
  full teleprompter script: spoken, conversational Azerbaijani in short lines,
  no bookish phrasing, no blanks (ask the user for any fact you need before
  writing). Personal-story videos (who I am, why I chose this path) get
  directions instead: talking points, an example sentence, blanks the expert
  fills in their own words. Every video also gets a separate montage plan
  (what footage goes where, on-screen cards).
- Follow the positioning section of the client's voice profile above all.

1. Work out which client this is for. If the user has not named one and the
   conversation has not already settled it, list the folders in
   `instagram-clients/` and ask. Never guess, and never carry one client's
   voice, numbers or plans into another client's work.
2. If the client has no folder yet, copy `instagram-clients/_template/` to
   `instagram-clients/<client>/` and fill in what you know.
3. Read `instagram-clients/<client>/voice.md` before writing anything, and
   write in the content language it names.

The agency shoots each expert once a week, 1-2 hours on a teleprompter, 5-10
videos per shoot. So a month is 4 shoots and roughly 25-35 reels, about one a
day, plus a carousel every week or two. The month plan is the source every
weekly package (`/ig-week`) draws from, so topics never repeat and the month's
offer is spread evenly instead of piled into one week.

## Before you plan

1. Read the client's voice profile, especially positioning, what is on sale
   this month, and the agency rules.
2. Read `audit.md` and any insights the user has sent. Lean toward what
   worked; drop what did not.
3. Read `log.md` if it exists, so nothing already posted comes back.
4. If you do not know what is on sale this month, ask. One question.

## The mix (per month, adjust to the client)

If the voice profile defines content pillars and a weekly rhythm, use those
instead of the default mix below, and give every week every pillar.

- ~60% expertise: methodology, practical how-to, one useful idea per video.
- ~20% conversion without selling: the program from the inside, a lesson
  moment, a graduate's professional result.
- ~10% the expert: who they are, why they work the way they do (personal
  story videos, written as directions, not teleprompter text).
- ~10% direct offer: registration, dates. Ads are separate and not planned here.
- Carousels: 3-5 save-worthy pieces (checklists, ready structures, task banks).

Every topic must pass the positioning: if it speaks to the wrong audience, turn
it around (e.g. a learner topic becomes "how to teach it").

## Output

A table, grouped by shoot week:

| # | week | format | on-screen title (2-5 words) | the one idea | script type |

script type is `prompter` (full text) or `directions` (personal story).
Below it, the carousel list with one line each. Draft in the chat; upload to
Drive only when the user approves.
