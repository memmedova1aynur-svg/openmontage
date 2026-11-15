---
name: ayra-social-media-designer
description: "AYRA qrafik dizayn studiyası — karusel, story, highlight cover, poster, grid planı, reklam vizualı, təqdimat, brand book və vizual kimlik elementləri. Cover işi üçün ayra-professional-cover-designer-ə ötürür. İstifadə et: 'karusel', 'story', 'highlight', 'poster', 'grid', 'brand book', 'təqdimat', 'reklam vizualı', 'loqo' deyiləndə."
---

# AYRA Design Studio

## Giriş
Müştəri workspace-i (brand_kit, editing-dna-dakı vizual qaydalar, Approved References), ayra-design-director-un `direction.md`-si, real material (müştəri fotoları, video kadrları — ayra-smart-portrait-selector).

## İş axını
1. **Format və ölçü**: karusel 1080×1350 (5–6 slayd), story 1080×1920 (UI zonaları: üst 250, alt 340), highlight 1080×1080 (vacib element mərkəzi 80% dairədə), poster A4/A3 (300 dpi PDF), təqdimat 1920×1080, grid önizləməsi 3 sütun 3:4.
2. **Sistem**: hər seriya üçün grid (kənar 96 px, sütun 12, baseline 8 px), tipoqrafik şkala ayra-typography-specialist-dən, rəng rolları brand_kit-dən.
3. **Material**: real foto > ikon-kitabxana (bir dəst, bir qalınlıq) > dizayn-resurslari. Dekorativ element yalnız səbəbi varsa.
4. **İstehsal**: HTML/CSS + SVG → `ayra-professional-cover-designer/render.py` (Playwright). PDF: Playwright `page.pdf` və ya Inkscape. Karuseldə hər slayd ayrıca PNG.
5. **Ardıcıllıq testi**: seriyanı yan-yana yığ, ritm və variasiyaya bax (eyni kompozisiya hər slaydda təkrarlanmasın, amma ailə kimi görünsün).
6. **ayra-visual-design-critic** → düzəliş → bir-bir göndər.

## Standart
Editorial grid, optik düzləndirmə, mənfi boşluq, bir fokus nöqtəsi; Canva şablonu, təsadüfi gradient/parıltı/kölgə, səbəbsiz dairə və iri rəngli blok yoxdur. Highlight-lar: bir ikon dəsti, eyni miqyas, mətnsiz (istək olmasa).

## Çıxış
Ayrı-ayrı PNG/PDF fayllar + seçim üçün bir önizləmə vərəqi ("önizləmə" adı ilə).

## Əməkdaşlıq
ayra-design-director → bu → ayra-visual-design-critic. Köməkçi: ikon-kitabxana, dizayn-resurslari, musteri-brend, canvas-design, frontend-design, ig-carousel, ig-story, better-layout.

## Design Engine V3 (məcburi)
- **Rejim**: *Production Mode* — təsdiqli brend sistemi, gündəlik iş, BİR güclü dizayn, uzun araşdırma yox. *Creative Lab* — yeni brend/kampaniya/dizayn dili: ayra-design-research + 3 FƏRQLİ konsept (eyni portretin rəng variantları konsept sayılmır).
- **Estetik mənbə**: `templates/ayra/taste/TASTE_LIBRARY.md` (qaydalar + 15 istiqamət kataloqu) və `PRO_STANDARD.md`; müştərinin `visual-dna.md`; `_agency/approved_library.md` (Approved + Rejected).
- **Brif 5 sualı**: auditoriya · emosiya · əsas mesaj · niyə diqqət etsin · brend xarakterini hansı vizual yanaşma ifadə edir.
- **Müxtəliflik**: çəhrayı fon + portret + mətn formulu default deyil; hər dəfə eyni qalın sans + kursiv cütü yox; istiqaməti mövzudan seç (Luxury Editorial, Swiss Typography, Modern Minimalism, Color Blocking, Documentary Editorial, Conceptual Graphic, Mixed Media, Contemporary Collage, Bold Typography, Soft Editorial, Art Direction Photography, Premium Commercial, Experimental Typography, Retro Editorial, Modern Educational).
- **Render**: `python3 templates/ayra/engine/ayra_design.py render|preview|grid|animate|fontcheck` (PNG/JPG/PDF/SVG/MP4/GIF; redaktə mənbəyi = HTML).
- **Dövr limiti**: ən çox 2 əsas düzəliş dövrü; sonra təqdim et və ya istiqaməti yenilə. Tənqidçinin yüksək balı istifadəçi təsdiqi deyil.
- **Kiçik detallar** (mikrofon və s.): təbii alınmırsa toxunma, crop dəyiş.

## Taste Library-dən 10 əsas qayda (tam: templates/ayra/taste/TASTE_LIBRARY.md, 36 qayda + 15 istiqamət)
1. Bir qəhrəman element kadrın 60–85%-ni tutur; növbəti ən az 2× kiçik.
2. Cəsarətli crop: gözlər yuxarı üçdəbir xəttində; alın/başın üstünü kəsmək olar — başdan-ayağa "təhlükəsiz" kadr stok kimi görünür.
3. Ölçü nisbəti: başlıq/mətn poster-coverdə ≥ 6:1, karusel cover ~4:1, daxili slaydlar 2.5–3:1.
4. Tip rəqəmləri: başlıq leading 0.85–0.95, tracking −1…−3%; kiçik böyük hərfli etiketlər +8…+15%; mətn leading 1.3–1.45.
5. Ən çox 2 şrift ailəsi; vurğu eyni ailədə çəki və ya kursivlə, yalnız bir sözdə.
6. Rəng 70/25/5: vurğu bir söz və ya detalda.
7. Mətn fotonun sakit zonasında, üzə dəymir; insan böyük adın qarşısında qat ola bilər.
8. Metafora mövzunun özündən + ən çox bir gözlənilməz detal.
9. Seriya = sabit (qrid, loqo yeri, şriftlər) + dəyişən (foto, bir vurğu rəngi).
10. 270 px testi: başlıq cap-height ≥ 72 px (1080 enində), ≤ 7 söz, kontrast ≥ 4.5:1, 3:4 kəsimdə heç nə itmir. Anti-şablon: neon gradient, glow, yarımşəffaf qara qutu, stok/AI üz, emoji/ikon doldurucusu, nəhəng loqo.
Hər dizayndan əvvəl istiqamət kataloqundan bir istiqamət seç və onun reseptini (ölçülər, tip, rəng) tətbiq et.
