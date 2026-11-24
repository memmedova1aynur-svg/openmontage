---
name: "ayra-brand-identity-designer"
description: "AYRA Brand Identity — loqo, wordmark, monogram, rəng sistemi, şrift sistemi, brand book (PDF), vizit kartı, stationery, brend təqdimatı. SVG vektor (Inkscape) + PDF (Playwright) + PNG. Yeni kimlik və ya əsas dəyişiklik = istifadəçi təsdiqi. İstifadə et: 'loqo', 'wordmark', 'monogram', 'brand book', 'vizit kartı', 'kimlik', 'brend sistemi' deyiləndə."
---

# AYRA Brand Identity Designer

## Alətlər
`python3 templates/ayra/engine/ayra_design.py render <page.html> <out> --size WxH --fmt png,pdf,svg` (SVG: mətn əyriyə çevrilir — loqo faylı üçün), Inkscape (vektor təmizləmə), `fontcheck` (Ə dəstəyi), `musteri-brend/brand.py`.

## İş axını (Creative Lab rejimi — həmişə)
1. **Brif**: mövqe (ayra-brand-strategist), auditoriya, şəxsiyyət 3 sifətlə, rəqiblərin vizual dili (yalnız ictimai).
2. **Araşdırma**: `templates/ayra/taste/TASTE_LIBRARY.md` → Brand identity bölməsi; 3 istiqamət seç.
3. **Eskiz**: hər istiqamət üçün 3–5 wordmark/monogram variantı yalnız qara-ağ (forma əvvəl, rəng sonra); 16 px favicon/avatar ölçüsündə oxunaqlılıq testi.
4. **Sistem**: rəng (rol + nisbət, məs. 60/30/10), şrift cütü (başlıq + mətn, Ə yoxlaması), qrid, fotoqrafiya üslubu, qrafik elementlər.
5. **Tətbiq**: Instagram avatar (dairə), highlight, post, vizit kartı (85×55 mm, PDF), brand book (8–16 səhifə PDF).
6. **Tənqid**: ayra-visual-design-critic (PRO_STANDARD.md).

## Çıxış
`brand/` qovluğu: `logo.svg`, `logo.png` (şəffaf), `brandbook.pdf`, `palette.json` → müştərinin `brand_kit.json`-una YALNIZ təsdiqdən sonra.

## Qaydalar
Loqo üçün AI şəkil generatoru yox; generik ikon + ad kombinasiyası yox; başqa brendin loqosuna bənzəyiş yoxlanır (audit-reference-originality).
