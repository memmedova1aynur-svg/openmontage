---
name: ig-story
description: >-
  Write the day's Instagram Stories - the frame-by-frame sequence, which
  stickers to use where, and the one that moves people into the DMs. Use when
  the user says "stories", "what do I post on my story", "story sequence",
  "poll idea", "I have nothing to story about", or wants to sell something
  without making a post about it.
---

# ig-story

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

Stories are not a smaller feed. The feed is how strangers find you. Stories are
how the people who already follow you decide whether you are a person worth
buying from, and they are the only surface on Instagram where a tap turns into
a conversation in one move.

Nobody outside your followers sees these, so the job is completely different:
depth, not reach.

## The daily shape

Three to seven frames a day. Beyond about seven, the tap-forward rate climbs
and the last frames play to nobody, which is exactly where people put the ask.

```
1       THE OPEN     something happening today, with a face or a hand in it.
2-3     THE MIDDLE   the actual content: the process, the result, the mistake.
4       THE ASK      one sticker. Poll, question box, quiz or link.
5       THE CLOSE    the answer, the outcome, or tomorrow's setup.
```

Put the ask at frame 4, not frame 7. Completion drops with every tap and the
ask should be seen by the people who are still there.

## The stickers, and what each is actually for

| sticker | job | use when |
| --- | --- | --- |
| **Poll** | the cheapest tap there is | you want volume of response, not information |
| **Question box** | harvesting the exact words people use | you need content ideas or objections, verbatim |
| **Quiz** | teaching by letting them be wrong | there is a common misconception in the niche |
| **Slider** | vibe check | nothing important. Fun, low value |
| **Link** | the only clickable surface besides the bio | there is somewhere real to go |
| **Countdown** | a deadline people can subscribe to | a launch, a live, a close date |
| **Add yours** | reach beyond your followers, occasionally | the prompt is one anyone in the niche can answer |

The question box is the most undervalued one in the list. Every answer is a
caption, a Reel hook or a DM opener written in the audience's own words. Feed
them to `/ig-reel` as formula #16.

## Rules

- **A face or a hand in the first frame.** Text on a coloured background gets
  tapped through, and the first frame decides whether the rest get watched.
- **One idea per frame.** Reading a paragraph on a story is not a thing anyone
  does.
- **Keep text inside the middle.** On 1080x1920, nothing above y=250 or below
  y=1600. The profile row sits on top and the reply bar sits underneath.
- **Talk to one person.** "You" singular. Stories are the closest thing to a
  DM that is not one.
- **Do not repost your own feed post to stories with no comment.** It is the
  single most ignored frame on the platform. If you are pointing at a post, say
  what happened in the comments and why it is worth going back for.
- **Sell on stories, not in posts.** Three frames of context, one frame of
  offer, one frame of proof. That sequence sells more than a feed post about
  the same thing and costs you no reach.

## The DM funnel, done honestly

The sequence that works: a story that names a problem, a question box or a poll
that lets people say "that's me", and then a reply to each person who answered.
The conversation starts because they spoke first.

Automated keyword DM replies are a real, supported feature for professional
accounts, through Instagram's own tools and approved partners. Bulk DMing
people who did not interact is not, and it is what gets accounts restricted.
The rule is simple: **they act first, then you reply.**

## Output

The frames in order, each with what is on screen, what is said, and which
sticker, plus what to do with the answers:

```
STORIES  ·  Tuesday  ·  5 frames

1  [selfie, walking]      "Third refund request this year. Same reason."
2  [screen recording]     the clause, highlighted
3  [talking]              "Approval is a feeling. Delivery is a date."
4  [poll]                 "Have you been burned by a late approval?"  Yes / Not yet
5  [text on photo]        "Reply and I will send you the clause."

After: everyone who votes Yes gets a reply. That is the whole funnel.
```

Nothing is posted. The user posts it.
