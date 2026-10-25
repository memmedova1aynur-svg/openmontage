---
name: ig-reel
description: >-
  Write an Instagram Reel from a raw idea - hook options off 26 formulas, the
  spoken script, the on-screen text, and a timed beat sheet - in the user's own
  voice and scored before they shoot it. Use whenever the user wants a Reel, a
  short-form video script, a hook, a voiceover, "make a reel about X", "what
  should I say in this video", or is about to record and does not have the
  first line yet.
---

# ig-reel

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

Agency rules, for every client, overriding anything below that conflicts:
- No agitation. Never show the expert's struggles, fears or private life.
  Present them professionally: decisions, knowledge, growth.
- One video, one topic. No jumping between events or subjects in one reel.
- Every video stands alone. No "part 1" or cliffhangers unless the user asks
  for a series.
- Scripts are directions, not lines to memorise: talking points per section,
  an example sentence, blanks the expert fills in their own words, and a
  separate montage plan (what footage goes where, on-screen cards).
- Follow the positioning section of the client's voice profile above all.

1. Work out which client this is for. If the user has not named one and the
   conversation has not already settled it, list the folders in
   `instagram-clients/` and ask. Never guess, and never carry one client's
   voice, numbers or plans into another client's work.
2. If the client has no folder yet, copy `instagram-clients/_template/` to
   `instagram-clients/<client>/` and fill in what you know.
3. Read `instagram-clients/<client>/voice.md` before writing anything, and
   write in the content language it names.

Turns one raw idea into a Reel that somebody finishes.

Two tools live in this folder and they both actually run. Use them. Do not
eyeball the hook and do not guess at the length.

```bash
python3 hookscore.py hooks.txt              # rank your hook options
python3 hookscore.py --hook "one line"      # score a single one
python3 beats.py script.txt --target 30     # timed beat sheet before you shoot
```

## Before you write

1. Read `instagram-clients/<client>/voice.md` if it exists. That is the user's voice
   profile: how they talk on camera, what they never say, who they are talking
   to. If it does not exist, ask for **three of their own reels**, transcribe or
   read them, infer the voice, and write the file. A script in the wrong voice
   is unusable, because they have to say it out loud.
2. Read `hooks.json` in this folder. 26 formulas, each with a template, a filled
   example, the on-screen version, what it is for, and how it gets ruined.
   Four of them are in there because they kept turning up in real hooks, not
   because they completed a pattern.
3. If the idea is thin, do not pad it. Ask one batched question: what happened,
   to whom, and what did it cost or return. A Reel needs one specific true
   thing. Get it before writing.
4. If `instagram-clients/<client>/swipe.md` exists, read it. `/ig-viral` writes that
   file, and it is the user's own evidence about which formulas are working in
   their niche right now. It beats the defaults in this file.

## The shape

A Reel is decided in the first two seconds and kept by the next five.

```
0:00 - 0:02   HOOK        the claim. Spoken line and on-screen line, written
                          separately. Motion in the first frame, not a static face.
0:02 - 0:07   THE STAKE   why this matters to the person watching. One line.
0:07 - ...    THE BODY    one idea per beat, and the frame changes every beat.
LAST 3s       THE PAYOFF  deliver what the hook promised, then the single ask.
LAST LINE     THE LOOP    echo one word from the hook so the replay lands clean.
```

Length: 15 to 45 seconds is the working range. Reels run to 3 minutes and
almost nobody should use it. Under 7 seconds the loop counts inflate and
nothing else does.

## The loop

**1. Pick three hooks, not one.** Run the idea through `hooks.json`, choose
three formulas that genuinely fit it, and write the spoken line plus the
on-screen line for each. Different formulas, not three rewrites of one.

**2. Score them.** Put the three spoken lines in a file, one per line, and run
`hookscore.py`. Show the user the ranking. If the top one is under 50, you do
not have the hook yet and no amount of editing fixes that.

**3. Write the script** on the winning hook. Plain spoken language, the way the
user actually talks. Contractions. Short lines. No sentence they would have to
rehearse.

**4. Time it.** Run `beats.py script.txt --target {length}`. Fix every flag:
a hook past 3 seconds, any beat over 4 seconds, a run of beats with nothing
concrete in them, no loop. Re-run until it is clean.

**5. Humanize it.** Run the script through `/ig-human` before showing it. A
written-sounding line is obvious the moment someone says it out loud.

**6. Print the block.** The script in a fenced block, the on-screen text as a
separate list with timings, and then:

```
REEL READY
hook:       #3 Nobody Tells You, scored 86 STRONG
length:     28.4s across 9 beats at 165 wpm
on-screen:  6 cards
humanizer:  4 artefacts stripped, human score 81 PASS
caption:    run /ig-caption next

Reply "yes" to log it, or tell me what to change.
```

**7. Never publish.** This skill produces a script. The user shoots it and
posts it. On "yes", append to `instagram-clients/<client>/log.md` with the date, the
hook formula used and the first line, so `/ig-audit` has a history later.

## On-screen text is a separate script

Write it separately, every time. It is read before it is heard.

- **Six words or fewer per card.** It is being read at arm's length by someone
  who is not listening yet.
- **The hook card is up at frame 1**, not after a beat of silence.
- **Keep it inside the safe zone.** On a 1080x1920 frame, nothing above y=230
  or below y=1440, and keep the right 230 pixels clear. The interface sits on
  top of everything outside that box: the caption, the action rail, the audio
  strip.
- **Never put the hook where the caption sits.** That is the bottom of the
  frame and it is covered.
- **Burn in captions for the body.** Most people watch muted first.

## Rules that make the difference

- **One idea per Reel.** If the script has two, you have two Reels. Say so.
- **Numbers over adjectives.** "$4,200" beats "a lot". If the user has not
  given a number, ask for one rather than writing around the hole.
- **Cut the intro.** No greeting, no "in this video", no name, no logo sting.
  The video starts at the sentence you would normally reach at second six.
- **Change the frame every beat.** A static shot for 8 seconds is where people
  leave, and `beats.py` will flag it.
- **One ask at the end.** Comment a keyword, save it, or follow. One.
- **Never fabricate.** No invented metrics, clients, revenue or outcomes under
  the user's name, even as a placeholder. If a number is needed and unknown,
  leave `{{your number}}` in the script and flag it.
- **Do not write a script around a trending audio the user cannot use.** If the
  idea needs the user's own voice, say so.

## Example

```
/ig-reel we cut proposal time from 5 hours to 20 minutes with one template
```

```
HOOKS  (scored)
  86  STRONG  #5  Time Collapse   "Proposals used to take me five hours. Twenty minutes now."
                                  on screen: 5 HOURS -> 20 MIN
  71  STRONG  #1  Cost Confession "I billed four hours a week for formatting. For two years."
                                  on screen: 2 YEARS WASTED
  54  OK      #9  The Steal       "Steal the proposal template that did it."
                                  on screen: STEAL THIS

Shooting #5: the ratio is believable, it reads in one glance on screen,
and the number is yours.
```
