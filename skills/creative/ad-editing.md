# Ad Editing — Commercials, Promos, UGC-Style Ads

## When to Use

Any video whose job is to sell or convert: product promos, app ads, brand
spots, UGC-style testimonials, launch videos, social ads. There is no
dedicated ad pipeline — run `hybrid`, `cinematic`, `talking-head`,
`avatar-spokesperson` or `animated-explainer` and apply this playbook on top
of `creative/editing-craft.md`.

## 1. Brief before edit

Write these down in the proposal; every edit decision is judged against them:

- **One audience** (who, what they already believe)
- **One message** (the single benefit, in one sentence)
- **One action** (the CTA: download, buy, visit, DM)
- **Proof** (demo, number, testimonial, before/after)
- **Platform + placement** (feed vs story, sound-on vs sound-off)

## 2. Structure

Pick one proven structure; don't invent a new one per ad.

| Structure | Beats | Best for |
|---|---|---|
| **Hook – Problem – Solution – Proof – CTA** | 0–3 / 3–8 / 8–18 / 18–25 / 25–30 s | Most direct-response ads |
| **Before / After / Bridge** | pain state → dream state → product is the bridge | Transformations, tools |
| **Demo-first** | product doing the thing in the first second, then why | Apps, gadgets, food |
| **UGC testimonial** | face + strong claim → story → product in use → CTA | Social proof |
| **Brand film** | emotion → reveal → logo/line | Awareness, launches |

Rules:
- **Product or result on screen within 2–3 s.** Viewers who leave at 3 s
  should still have seen what it is.
- **Show, then say.** Demo footage beats claims; every claim gets a visual proof.
- **Brand early but not first.** Logo/name by ~5 s (supers or packaging in
  shot), full logo lock-up only at the end.
- **One CTA**, said and shown, in the last 3–5 s, with the end card held
  ≥ 1.5 s.

## 3. Hooks that work in the first 1–3 seconds

Pattern-break visual (unexpected motion, extreme close-up, a mess being
cleaned), a direct question to the viewer, a bold number, the result first
("this took 4 seconds"), a contrarian line, or the product in the hand moving
toward camera. Write 3–5 hooks per ad and cut **hook variants** — the body
can stay identical.

## 4. Cutting style

- Average shot 0.8–2.5 s; build in accelerating runs into the reveal, then one
  held hero shot (1.5–3 s) of the product.
- Every cut on a beat or an action; the reveal lands on the drop.
- **Hero shots**: slow push or orbit, clean background, light sweep/glint,
  shallow depth of field. Product always sharp, colours true to the brand.
- Speed ramps (100 % → 30 % → 100 %) on the money moment, with a whoosh/hit.
- Supers (on-screen text) carry the message for sound-off viewing: 3–6 words,
  big, high contrast, one idea per super.
- Captions are mandatory for social placements (85 %+ watch muted).

## 5. Sound

- Music chosen for the edit's tempo; cut to the music, and edit the music so
  the drop meets the reveal and the button meets the CTA.
- Sound design is what makes an ad feel expensive: whooshes on every
  transition, product foley (click, pour, snap, unbox), riser before the
  reveal, sub hit on the logo.
- VO: confident, close-mic, slightly faster than conversational (160–180 wpm)
  — see `creative/vo-production.md`.
- Mix to −14 LUFS / ≤ −1 dBTP for social; −23/−24 LUFS for broadcast.

## 6. Versions (deliverables an agency would ship)

| Version | Notes |
|---|---|
| 30 s / 15 s / 6 s cut-downs | 6 s = hook + product + logo only |
| 9:16, 1:1, 4:5, 16:9 | Re-frame each; never just letterbox. Keep supers inside each format's safe zone |
| Hook variants (A/B/C) | Same body, different first 3 s |
| Sound-off version | Supers carry the full message |
| Clean version | No supers, for re-use |

Name files `brand_campaign_len_ratio_variant_v01.mp4`.

## 7. Legal / platform hygiene

- No unlicensed music or logos; claims must be provable.
- Respect platform text-overlay and UI safe zones.
- Avoid flashing faster than 3 Hz (seizure safety).

## Quality Checklist

- [ ] Product/result visible by 3 s; brand identified by ~5 s
- [ ] Message understandable with sound off
- [ ] Every claim has a visual proof
- [ ] Reveal on the music drop; CTA on the button; end card ≥ 1.5 s
- [ ] SFX on every transition and product action
- [ ] Cut-downs and aspect ratios re-framed, not letterboxed
- [ ] `delivery_qc` (format `ad`) has no `fail`
