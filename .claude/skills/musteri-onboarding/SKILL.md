---
name: musteri-onboarding
description: Premium müştəri onboarding-i — yeni müştəriyə göndərilən Brend Anketi (PDF + doldurulan Word), doldurulmuş anketdən 1 iş günündə müştəri qovluğu, brand.md/voice.md və müştəriyə təqdim olunan Strateji paket PDF (brend xülasəsi, auditoriya, mövqe, səs, vizual, Instagram profili, kontent sistemi, 3 aylıq yol xəritəsi, 30 günlük təqvim, ilk həftənin materialları, iş rejimi). "yeni müştəri", "anket", "brif", "onboarding", "strateji paket", "müştəri anketi doldurdu" deyiləndə işlət.
---

# Müştəri onboarding-i (Anket → 24 saat → Strateji paket → İş rejimi)

## Prinsip
Strategiyanı, rəngləri, çəkiliş mövzularını **biz** qərarlaşdırırıq. Anket müştərinin keçmişini, diplomlarını, büdcəsini soruşmur — yalnız qərarlarımızı istiqamətləndirən üstünlükləri və sərhədləri: sevdiyi/sevmədiyi rənglər, əhval, kamera rahatlığı, göstərmək istəmədikləri, mövzular, mətni kim yazır, story-ləri kim paylaşır, təsdiq.

## A. Müştəriyə gedən sənədlər
```bash
python3 .claude/skills/musteri-onboarding/scripts/build_anket.py <outDir>            # Brend_Anketi.pdf + .docx (23 sual, çoxu seçimli)
python3 .claude/skills/musteri-onboarding/scripts/build_doc.py .claude/skills/musteri-onboarding/assets/xidmetler.json <outDir>/Xidmet_paketleri.pdf
```
- Suallar: `assets/anket.json`; paketlər: `assets/xidmetler.json` (Start / Pro / Premium, mütləq işlər, əlavə xidmətlər, daxil olmayanlar, qaydalar). Qiymətlər `[qiymət]` — yalnız Aynur yazır, uydurma.
- `build_doc.py` ümumi premium sənəd mühərrikidir (təklif, hesabat, brend kitabı üçün də): blok tipləri skriptin başında yazılıb.
- Aynurun öz brend kitabı: `instagram-clients/aynur-memmedova/brandbook.json` (məxfi) → `build_doc.py`.
- Faylları tək-tək göndər (zip yox).

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
