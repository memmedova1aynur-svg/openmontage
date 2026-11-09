---
name: musteri-onboarding
description: Premium müştəri onboarding-i — yeni müştəriyə göndərilən Brend Anketi (PDF + doldurulan Word), doldurulmuş anketdən 1 iş günündə müştəri qovluğu, brand.md/voice.md və müştəriyə təqdim olunan Strateji paket PDF (brend xülasəsi, auditoriya, mövqe, səs, vizual, Instagram profili, kontent sistemi, 3 aylıq yol xəritəsi, 30 günlük təqvim, ilk həftənin materialları, iş rejimi). "yeni müştəri", "anket", "brif", "onboarding", "strateji paket", "müştəri anketi doldurdu" deyiləndə işlət.
---

# Müştəri onboarding-i (Anket → 24 saat → Strateji paket → İş rejimi)

## A. Anketi göndər
```bash
python3 .claude/skills/musteri-onboarding/scripts/build_anket.py <outDir>
```
`Brend_Anketi.pdf` (təqdimat, çap/baxış) və `Brend_Anketi.docx` (müştəri cavabları boz qutulara yazır) yaranır. Suallar tək mənbədədir: `assets/anket.json` — sual əlavə/dəyişmək üçün yalnız onu redaktə et. Müştəriyə hər iki faylı tək-tək göndər (zip yox).

## B. Anket geri gəldi (docx, pdf, ekran şəkli və ya mesaj mətni)
1. Cavabları oxu (docx: `python-docx`; şəkil: gözlə oxu). Müştərinin adını, sahəsini, linklərini çıxar.
2. Qovluq: `sh .claude/skills/marketinq-sistemi/scripts/new_client.sh <slug> "<Ad>"`. Anketin özünü qovluğa `anket_cavablari.<ext>` kimi qoy.
3. **brand.md** və **voice.md**-ni YALNIZ anket cavablarından və müştərinin açıq səhifəsindən doldur. Cavabı olmayan yer: `[doldurulmalı]`. Fakt, rəqəm, ünvan, nəticə, rəy uydurma.
4. Instagram linki varsa: `ig-analiz` (son paylaşımlar, nə işləyir) və `ig-profile` (bal və boşluqlar). Rəqib linkləri varsa: `competitor-branding`.
5. Strategiya üçün köməkçi skill-lər: `target-audience` (personalar), `brand-positioning` (mövqe cümləsi), `brand-voice` (ton), `brand-identity` (vizual), `personal-brand` (şəxsi brenddirsə), `ig-month` (30 gün), `ig-reel`/`social` (ilk həftə).

## C. Strateji paket
1. `assets/paket_numune.json` sxemini kopyala → `instagram-clients/<slug>/paket.json` və doldur. Sahələr: agency, client, date, summary, personas, positioning, voice, visual.palette ([ad, hex]), profile, pillars (share cəmi 100), rhythm, roadmap (3 ay), calendar (30 gün), week1, process, next, missing.
   - Kontent rolları və ritm müştərinin anketdəki imkanlarına uyğun olsun (çəkiliş tezliyi, kim kamerada).
   - `missing` — anketdə cavabı olmayan və müştəri təsdiqi gözləyən hər şey. Uydurma əvəzinə buraya yaz.
   - Satış CTA-ları yalnız müştəri satış mərhələsindədirsə.
2. Render: `node .claude/skills/musteri-onboarding/scripts/build_paket.js instagram-clients/<slug>/paket.json <out>/Strateji_paket_<Ad>.pdf`
3. PDF-ə səhifə-səhifə bax (`pdftoppm -r 50 -png`): boş səhifə, kəsilən cədvəl, uzun sözlər.
4. Müştəriyə yalnız Aynur təsdiqləyəndən sonra göndərilir.

## D. İş rejiminə keçid
- `context.md`-yə yaz: anket tarixi, paket versiyası, təsdiq statusu, çatışmayanlar.
- `plan_status.md` yarat: 30 günlük təqvim → həftəlik istehsal (`ig-week`, `post-studio`, `reels-pro`).
- Hər ayın sonunda: `ig-audit` + paketin "3 aylıq yol xəritəsi" ilə müqayisə → növbəti ay.

## Keyfiyyət
- Paket müştəri üçündür: Azərbaycan dilində, səliqəli, rəqəmlər yalnız anketdən. "Nümunə" faylındakı Dental Smile uydurmadır — heç vaxt real müştəri materialına köçürmə.
- Agentlik görünüşü sabitdir (plum/laym, Aynur Məmmədova · Brend Menecment); müştərinin rəngləri yalnız "Vizual istiqamət" bölməsində.
