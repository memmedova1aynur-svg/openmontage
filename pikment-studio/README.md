# Pikment Creative Studio

Permanent production system for Pikment (pikment.az) video work: Remotion compositions, ElevenLabs voice, beat-locked music and SFX.

```
pikment-studio/
  brand/        official logo (SVG, from pikment.az), extracted site facts (facts.json)
  tools/        capture_site.js, extract_site_facts.py, mix_launch.py
  docs/         BRAND_GUIDE, COMPLIANCE, VOICE_GUIDE, AUDIO_GUIDE, COMPONENTS
  templates/    brief + storyboard templates
  productions/  one folder per video (brief, storyboard, notes)
remotion-composer/src/pikment/        reusable library (brand tokens, fonts, motion, Logo, Kit)
remotion-composer/src/productions/    one composition + timeline JSON per video
```

Workflow: brief -> storyboard -> `capture_site.js` for real UI -> voice takes -> `mix_launch.py`-style mix -> Remotion render -> QC -> deliver.
