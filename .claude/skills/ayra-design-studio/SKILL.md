---
name: ayra-design-studio
description: "AYRA qrafik dizayn studiyası — karusel, story, highlight cover, poster, grid planı, reklam vizualı, təqdimat, brand book və vizual kimlik elementləri. Cover işi üçün ayra-professional-cover-designer-ə ötürür. İstifadə et: 'karusel', 'story', 'highlight', 'poster', 'grid', 'brand book', 'təqdimat', 'reklam vizualı', 'loqo' deyiləndə."
---

# AYRA Design Studio

## Giriş
Müştəri workspace-i (brand_kit, editing-dna-dakı vizual qaydalar, Approved References), ayra-art-director-un `direction.md`-si, real material (müştəri fotoları, video kadrları — ayra-smart-portrait-selector).

## İş axını
1. **Format və ölçü**: karusel 1080×1350 (5–6 slayd), story 1080×1920 (UI zonaları: üst 250, alt 340), highlight 1080×1080 (vacib element mərkəzi 80% dairədə), poster A4/A3 (300 dpi PDF), təqdimat 1920×1080, grid önizləməsi 3 sütun 3:4.
2. **Sistem**: hər seriya üçün grid (kənar 96 px, sütun 12, baseline 8 px), tipoqrafik şkala ayra-typography-specialist-dən, rəng rolları brand_kit-dən.
3. **Material**: real foto > ikon-kitabxana (bir dəst, bir qalınlıq) > dizayn-resurslari. Dekorativ element yalnız səbəbi varsa.
4. **İstehsal**: HTML/CSS + SVG → `ayra-professional-cover-designer/render.py` (Playwright). PDF: Playwright `page.pdf` və ya Inkscape. Karuseldə hər slayd ayrıca PNG.
5. **Ardıcıllıq testi**: seriyanı yan-yana yığ, ritm və variasiyaya bax (eyni kompozisiya hər slaydda təkrarlanmasın, amma ailə kimi görünsün).
6. **ayra-design-critic** → düzəliş → bir-bir göndər.

## Standart
Editorial grid, optik düzləndirmə, mənfi boşluq, bir fokus nöqtəsi; Canva şablonu, təsadüfi gradient/parıltı/kölgə, səbəbsiz dairə və iri rəngli blok yoxdur. Highlight-lar: bir ikon dəsti, eyni miqyas, mətnsiz (istək olmasa).

## Çıxış
Ayrı-ayrı PNG/PDF fayllar + seçim üçün bir önizləmə vərəqi ("önizləmə" adı ilə).

## Əməkdaşlıq
ayra-art-director → bu → ayra-design-critic. Köməkçi: ikon-kitabxana, dizayn-resurslari, musteri-brend, canvas-design, frontend-design, ig-carousel, ig-story, better-layout.
