# voice.md

The voice profile for one client account. Copy this whole `_template/` folder to
`instagram-clients/<client>/` and fill it in. Every `ig-*` skill reads it before
writing for this client.

If you would rather not fill it in by hand, send Claude three of the client's
own reels or captions and say "write the voice.md for <client> from these".
That works better than guessing at the answers.

This file matters more on Instagram than anywhere else, because someone has to
say the words out loud. A line the client would never say is not a draft, it is
a retake.

---

## The account

- **Client / brand name:**
- **Handle:**
- **Content language:** (e.g. Azerbaijani, Russian, English, or a mix and when)
- **What they do, in one sentence:**
- **Who they are talking to:** (be specific: "mothers in Baku with kids under
  five", not "families")
- **What they sell:**
- **Who appears on camera:** (the owner / staff / a hired presenter / faceless)

## What they sound like

- **Three of their own reels or captions that sound most like them:** (paste them)
- **On camera they are:** (fast and loud / dry / calm / funny / deadpan)
- **Words they actually use:**
- **Words they would never say out loud:**
- **Swearing:** (yes / mild / no)
- **Emoji in captions:** (never / one, rarely / freely)
- **Voiceover or to-camera:**
- **Pace:** (words per minute, if timed. `beats.py --wpm` uses this. Most
  people are between 150 and 200.)

## Their positions

Three to five things the client believes that some of their audience does not.
These are where the good reels come from.

1.
2.
3.

## Off limits

- **Topics they do not post about:**
- **Customers, numbers or names that cannot be said publicly:**
- **Claims they are not allowed to make:** (regulated industry, health claims,
  pricing rules)

## Proof they can use

Real numbers, outcomes and stories the client is happy to put their name on.
The skills will never invent one, so if this section is empty, every draft
comes back with `{{your number}}` in it.

-
-
-

## The ask

- **Keyword CTA, if they use one:** (one word, sayable, no spaces)
- **What the keyword sends them:**
- **Where the link goes:**
