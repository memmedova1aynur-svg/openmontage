---
name: ig-repurpose
description: >-
  Turn one long asset - a YouTube video, podcast, livestream, newsletter, blog
  post or client call - into a week of reels and carousels. Use when the user
  says "repurpose this", "turn this into reels", "I have a video/podcast/
  transcript", "cut this up", or pastes something long and wants it on
  Instagram.
---

# ig-repurpose

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

One good long asset contains four to six posts. Most people extract one and
throw the rest away.

## Input

A transcript, an article, a newsletter, a script, a call summary, a livestream.
If the user gives a URL and this session has a transcript tool, use it;
otherwise ask them to paste. Read the whole thing before extracting anything.

If the source is a video the user owns, ask for the file too. A Reel built on
their own footage beats one built on their own words read again.

## Extract, do not summarise

A summary of a video is not a Reel. Nobody wants the summary. Go through the
asset and pull out the things that stand alone:

| pull | what it is |
| --- | --- |
| **Claims** | every sentence that would start an argument |
| **Numbers** | every figure, cost, duration, percentage |
| **Stories** | every moment with a person, a scene and a cost |
| **Mechanisms** | every "the way this actually works is..." |
| **Mistakes** | every admission of something that went wrong |
| **Lines** | every sentence already quotable as-is |

List what you found, with counts, before writing anything. If the asset yields
fewer than four items, it is thin, and four posts squeezed out of it will be
thin too. Say that.

## Then pick the format per extract

Not everything is a Reel.

- **Claim, mistake, story** to a Reel. They need a voice and a face.
- **Mechanism, numbered list** to a carousel. They need to be re-read.
- **A quotable line** to a story frame, not a post.

## Then build the week

Each extract becomes one post and each post stands completely on its own. The
viewer has not seen the source and never will. Never write "as I said in my
latest video". The post is the thing.

Assign a hook formula from `ig-reel/hooks.json` to each and vary them. Five
posts from one source with the same hook shape reads as a content mill, because
it is one.

If the source is the user's own video, **use the actual footage**. The clip
where they said the thing, with the real reaction in it, beats a re-record
every time. Cut on the sentence, not on the breath.

Order across the week so the strongest claim goes first, the story lands
midweek, and the mechanism goes last, when the people who liked the earlier
ones are watching for it.

## Output

```
SOURCE: "Why we killed discovery calls" (42 min podcast, 8,900 words)

FOUND  5 claims, 9 numbers, 3 stories, 4 mechanisms, 2 mistakes, 7 quotable lines

WEEK
TUE  REEL      #2  Negative Command  Stop running discovery calls
                                     use the 14:20 clip, he laughs at the end
WED  CAROUSEL  Job B caption         The 4-question form that replaced the call
FRI  REEL      #21 Mid-Sentence      "...and he asked for a refund nine days later"
SUN  REEL      #5  Time Collapse     Six hours a week back, one deleted link

Say "write Tuesday" and I will draft it.
```

Then draft on request, one at a time, each through `/ig-reel` and `/ig-human`.
Do not dump four finished scripts at once. They will all sound the same and the
user will shoot none of them.
