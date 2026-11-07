---
name: ig-analiz
description: Instagram açıq profil linkindən səhifə analizi — son 30 paylaşımın mövzu, format, başlıq, tarix, əsas mesaj və təkrarlanan istiqamətləri; Reels transkripti, karusel OCR; mövzu xəritəsi, boşluqlar və 10 yeni ideya, hər müşahidə paylaşım linki ilə. İstifadəçi Instagram profil linki göndərib "analiz et", "səhifəni təhlil et", "rəqib analizi" deyəndə işlət.
---

# Instagram səhifə analizi

Instagram parolu, cookie və ya hesab girişi **istənilmir və istifadə olunmur**. Məlumat Apify Instagram Scraper (açıq profil) ilə toplanır.

## Addımlar
1. `python3 templates/expert-reels/pro/ig_analyze.py fetch <profil_linki>` — default son 30 paylaşım, xərc tavanı $0.25 (`--limit`, `--max-usd`). Keş varsa yalnız yeni paylaşımlar gəlir.
   - Apify açarı yoxdursa: `request_credential` (host `api.apify.com`, Authorization: Bearer). Açarı söhbətə yazmağı istəmə.
2. `... media <hesab>` — Reels: transkript (ElevenLabs Scribe; kvota yoxdursa whisper — "zəif keyfiyyət" kimi işarələnir), karusel/şəkil: OCR (tesseract aze+eng, "yoxlanmalı"). `--stt-min` transkript büdcəsi (default 10 dəq). Emal olunan paylaşım təkrar emal olunmur.
3. `... digest <hesab>` → `instagram-clients/_analysis/<hesab>/digest.md` + `covers.jpg`. Digest-i və üz qabığı vərəqini oxu; OCR şübhəlidirsə müvafiq şəkli özün aç və yoxla.

## Hesabat (Claude yazır)
- **Mövzu xəritəsi:** mövzu qrupları → paylaşım sayı, format, nümunə linklər.
- **Hər paylaşım:** tarix, format, başlıq/hook, əsas mesaj, mənbə (caption / transkript / OCR).
- **Təkrarlanan istiqamətlər** və **boşluqlar** (auditoriyanın ehtiyacı olub, səhifədə olmayan mövzu/format).
- **10 yeni ideya:** əvvəlki paylaşımları təkrarlamır; hər biri hansı boşluğu doldurduğunu və hansı paylaşım(lar)a əsaslandığını linklə göstərir.
- Hər müşahidə ən azı bir paylaşım linki ilə əsaslandırılır. "YALNIZ CAPTION oxunub" işarəli paylaşımları açıq yaz. Əlçatan olmayan məlumatı (baxış sayı, video məzmunu) uydurma.
