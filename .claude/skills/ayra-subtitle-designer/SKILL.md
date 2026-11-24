---
name: "ayra-subtitle-designer"
description: "AYRA Post-Production — Subtitle Designer. Azərbaycan dilində düzgün yazılmış, brend üslubunda subtitrlər: dəqiq transkript + glossary_az.json + insan oxunuşu, sətir/söz qaydaları, vurğu sözü, ASS (videoya yandırılan) və ayrıca SRT faylı. Hər videoda eyni subtitr üslubu məcburi deyil — Editing DNA + konsept. İstifadə et: hər montajda, 'subtitr', 'altyazı', 'SRT', 'yazı xətası' deyiləndə."
---

# AYRA Subtitle Designer

## Alətlər
- engine.py `write_ass` (yandırılan ASS, brend rəngi), `caps_check.py`, `words_check.py`, `templates/expert-reels/pro/glossary_az.json`.
- `python3 .claude/skills/ayra-subtitle-designer/srt_export.py <video|words.json> <out.srt> [--ref mətn.txt]` — ayrıca SRT (video verilsə faster-whisper ilə söz vaxtları; `--ref` təsdiqli mətnə görə söz-söz düzəliş).

## Qaydalar
- Mətn: ASR yazılışı birbaşa getmir — glossary + təsdiqli ssenari/spec mətni ilə düzəldilir; ad və terminlər (laktasiya, ərgənlik) yoxlanır.
- Ekranda 2–4 söz (reels), ən çox 2 sətir, sətir ≤ 22 simvol; cümlə sonunda bölünür.
- Vaxt: söz başlanğıcından 80 ms əvvəl görünür, ən az 0.6 s qalır.
- Yer: üz zonasından aşağı, Reels UI-dan yuxarı (y ≈ 1350–1450 / 1920); qrafika kartı ilə toqquşmur.
- Üslub: brend palitrası; vurğu sözü bir üsulla (blok və ya rəng). `lang="az"` / `az_upper` — "İ".
- SRT ayrıca verilir (Instagram-a yükləmək və ya arxiv üçün), yandırılmış subtitrsiz versiya istəniləndə `clean.mp4`.

## Çıxış
Yandırılmış subtitr + `video.srt` + yazılış yoxlama nəticəsi.
