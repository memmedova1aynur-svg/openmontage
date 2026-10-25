---
name: ig-audit
description: >-
  Post-mortem on what the user has already posted - which reels actually
  worked, why, and what to stop making. Use when the user pastes their
  Instagram insights or past posts and asks "what's working", "why did this
  flop", "read my analytics", "audit my content", or wants to know what to do
  more of.
---

# ig-audit

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

The only honest source of what works for an account is that account. Every
rule in every Instagram guide, including the ones in this pack, is a prior.
The user's own last 30 posts are the evidence.

## Input

Ask for whichever the user has:

- Insights per post: views, reach, interactions, watch time, saves, shares,
  follows, and the non-follower share of reach. Screenshots are fine.
- Or the retention graph for their best and worst recent reels. This one
  screenshot is worth more than the rest combined.
- Or just the posts and their view counts, which is enough for a first pass.

Also read `instagram-clients/<client>/log.md` if it exists, since it records which
hook formula each post used.

## What to actually measure

Raw views is the least useful number on the page, because it is mostly a
function of how many people already follow the account. Compute these instead
and show the working:

| metric | how | what it tells you |
| --- | --- | --- |
| **Outlier multiple** | views / the account's own median views | whether this was a real hit or a normal day |
| **Non-follower reach** | % of reach from people who do not follow | whether it travelled at all |
| **Hold at 3s** | viewers still there at 3s / viewers who started | whether the hook worked. This is the hook's grade. |
| **Average watch time** | straight from insights | whether the middle worked |
| **Sends per reach** | shares / reach | the strongest single signal you can earn. A send is a person putting their name on it. |
| **Follows per reach** | follows / reach | whether the profile converted the attention |

Rank by outlier multiple and sends per reach, not views. A reel with 4,000
views and 90 sends beat the one with 60,000 views and 11.

## Then find the pattern

With the top five and bottom five side by side, look for what separates them,
and be willing to conclude something the user will not like:

- **Hold at 3 seconds.** If the top and bottom differ here, it is the hook and
  nothing else, and everything downstream is a distraction.
- **Hook formula.** Which ids from `ig-reel/hooks.json` are in the top five?
- **Format.** Reel, carousel, single image.
- **Length.** Group into under 15s, 15 to 30s, 30 to 60s, over 60s.
- **Theme.**
- **Whether the user replied to comments in the first hour.**
- **Day and time.** Check this **last** and only if the others show nothing.
  It is almost never the cause and it is where people want it to be.

State the finding as a claim with the evidence attached, and say how confident
it is. With 30 posts you can see a pattern. With 6 you cannot, and saying so is
better than inventing one.

## The distinction that saves people months

**A reel that gets views and no follows is not a failed reel, it is a profile
problem.** A reel that gets no views is a hook problem. Separate the two before
recommending anything. If non-follower reach is high and follows per reach is
low, stop rewriting hooks and go to `/ig-profile`.

## Output

```
AUDIT  ·  31 posts  ·  Jun 12 - Sep 5  ·  median views 4,100

TOP 5 BY OUTLIER MULTIPLE
  18.2x  #3  Nobody Tells You   74,600 views  62% non-follower  hold@3s 71%  128 sends
   6.4x  #1  Cost Confession    26,300 views  48% non-follower  hold@3s 64%   71 sends
  ...

BOTTOM 5
   0.3x  #11 Numbered            1,200 views  9% non-follower   hold@3s 31%    2 sends
  ...

WHAT THE DATA SAYS
1. Hold at 3 seconds is the whole story. Top five average 66%, bottom five 33%.
   Everything else you are worried about is downstream of the first two seconds.
2. The posts where you were the one who looked bad: mean 8.1x vs 0.9x for
   everything else. n=5. Strongest signal here and it is not close.
3. Tool listicles get views and nothing else. High reach, no sends, no follows.
   Three of your bottom five.
4. Day of week shows nothing. Your Tuesday and Friday means are inside the
   noise. Stop optimising it.

STOP: listicles.
DO MORE: the ones with a cost you paid and a number attached.
```

Then hand the conclusions to `/ig-plan` so next week is built on the user's own
evidence rather than on defaults, and to `/ig-viral` so the swipe file gets
filtered to the formulas that work for this account specifically.
