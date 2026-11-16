---
name: ayra-creative-intelligence
description: AYRA Creative Intelligence System — istənilən müştəri üçün «müştəri + mövzu + format» verildikdə tam kreativ istehsal axınını avtomatik idarə edir — BRAND PROFILE → MARKETING STRATEGY → CREATIVE DIRECTION → PINTEREST RESEARCH → DESIGN ARCHITECTURE → ASSET CURATION → DESIGN → VISUAL CRITIQUE → REFINEMENT → FINAL EXPORT. Cover, post, karusel, story, reklam, grid. Mövcud skill-ləri ardıcıllıqla çağırır, təsdiq gözləmədən işləyir, yalnız keyfiyyət yoxlamasından (hər meyar ≥8) keçmiş nəticəni təqdim edir. İstifadə et: hər dizayn tapşırığında, «hazırla», «dizayn et», «cover», «post», «karusel» deyiləndə.
---

# AYRA Creative Intelligence System

Bu skill yeni alət deyil — **mövcud skill-ləri bir axına bağlayan dirijordur.** Hər mərhələnin dərin qaydası öz skill-indədir; burada ardıcıllıq, keçid şərtləri və çıxış faylları var.

| # | Mərhələ | Skill | Çıxış (scratchpad/<iş>/) |
|---|---|---|---|
| 1 | Brand profile | `ayra-brand-strategist` + `instagram-clients/<m>/brand_profile.md` | — (oxu) |
| 2 | Marketing strategy | `ayra-copywriter` (§ Strategiya) | `brief.md` |
| 3 | Creative direction | `ayra-design-director` (§ Kreativ direktor sualları) | `brief.md` |
| 4 | Pinterest research | `ayra-pinterest-research` (3 istiqamət) | `pin/*/sheet.jpg`, `refs.md` |
| 5 | Design architecture | **bu skill §5** | `refs.md` (struktur cədvəli) |
| 6 | Asset curation | `ayra-visual-research` (§ Kurator meyarları) | `assets.md` + kitabxana |
| 7 | Design | `templates/ayra/engine/ayra_design.py render` (HTML/CSS/SVG) | `out/*.png` |
| 8 | Visual critique | `ayra-visual-design-critic` (10 meyar, müstəqil Agent) | `critique.md` |
| 9 | Refinement | <8 olan hər meyar üçün konkret düzəliş, ən az 1 tam dövrə | `out/*_v2.png` |
| 10 | Final export | `scripts/grid_check.py` + ölçü yoxlaması | `final/` |

**Təsdiq gözləmə.** Sual yalnız: (a) müştəriyə aid fakt yoxdur (qiymət, tarix, öz metodu), (b) qərar brend istiqamətini dəyişir (yeni rəng/şrift/loqo). Qalan hər şeyi özün həll et.

## 1. Brand profile
`instagram-clients/<m>/brand_profile.md` oxu (yoxdursa `_template/brand_profile.md`-dən yarat, mövcud `brand_kit.json`, `visual-dna.md`, `voice.md`, `strategiya.md`-dən doldur). **Bir müştərinin rəngi/üslubu başqasına keçmir.** İstifadəçinin hər düzəlişini dərhal profilin «Qərarlar jurnalı»na yaz.

## 2–3. Strategiya və kreativ istiqamət — `brief.md`
Yaz (qısa): kim üçün · onun konkret problemi · məqsəd (reach / trust / value / sales) · bir cümləlik mesaj · **niyə dayanıb baxsın?** · hansı hiss · vizual növ qərarı (real insan / obyekt foto / illüstrasiya / sırf tipoqrafiya — səbəbi ilə) · **kreativ ideya** (bir cümlə; «rəngli fonda mətn» ideya deyil) · 3–5 başlıq variantı + seçim səbəbi.

## 4. Pinterest — üç ayrı istiqamət
1. **Dizayn** (kompozisiya, tipoqrafiya, grid), 2. **Fotoqrafiya** (işıq, rakurs, obyekt düzümü), 3. **Brend** (sahənin vizual kimliyi). Hər biri üçün sahəyə və konkret mövzuya uyğun sorğu (məs. «Montessori toys editorial product photography», «household objects flat lay editorial photography», «typographic poster design bold word»). 15–20+ nəticə, 3–5 seçim.

## 5. Design Architect — referansın strukturu
Hər seçilmiş referans üçün `refs.md`-də cədvəl:
| sual | cavab |
|---|---|
| Vizual fokus haradadır? | |
| Başlıq kadrın neçə %-ni tutur, harada? | |
| Başlıq / ikinci mətn ölçü nisbəti (məs. 150px : 46px ≈ 3.3×) | |
| Foto ↔ mətn əlaqəsi (üst-üstə, yan-yana, çərçivədə, mətn fotonun içində) | |
| Simmetriya / asimmetriya | |
| Boşluq necə işləyir | |
| Rəng nisbəti (fon / əsas / vurğu %) | |
| Peşəkar göstərən əsas detal | |
Sonra: **«götürdüyüm prinsip → bizim dizaynda necə»** — bir cümlə. Referansın mətni, loqosu, xüsusi forması kopyalanmır.

**Mühərrik məhdudiyyəti dizaynı sadələşdirmir:** HTML/CSS (grid, clip-path, mix-blend-mode, -webkit-text-stroke, SVG filter/feDisplacement, mask), Pillow, rembg birlikdə istifadə olunur. Lazım olan effekt yoxdursa — əvvəl CSS/SVG-də qur, alınmırsa Pillow-da piksel səviyyəsində et.

**Şablon qadağası:** eyni layout-un rəng/mətnini dəyişib seriya «dizayn» hesab edilmir. Hər iş mövzudan doğan öz kompozisiyasını alır; seriyada vahidlik yalnız brend elementləri (rəng, şrift, wordmark, kənar boşluqları) ilə təmin olunur.

## 7. Dizayn qaydaları (bütün müştərilər)
- Bir əsas fokus; başlıq/ikinci mətn nisbəti ≥ 2.5×; kənar boşluğu ≥ 72px (1080 en).
- Üzü heç nə örtmür; müştərinin üz cizgiləri dəyişdirilmir; AI ilə müştəri şəkli yaradılmır.
- Bəzək (dairə, stiker, ulduz, lent) yalnız ideyaya xidmət edirsə; məqsədsiz forma yoxdur.
- Real şəkillər eyni işıq/kölgə dilində (eyni drop-shadow, eyni fon), eyni miqyas məntiqində.
- Azərbaycan hərfləri: Ə İ Ş Ğ Ç Ö Ü — böyük hərfdə diakritika üst sətirlə toqquşmamalıdır.

## 8–9. Tənqid və təkmilləşdirmə
`ayra-visual-design-critic` 10 meyarla (müstəqil Agent — kontekstsiz göz) qiymətləndirir. **Hər meyar ≥ 8** olmalıdır; aşağı olan hər meyar üçün konkret problem → konkret düzəliş → yenidən render → yenidən bax. Ən az 1 tam düzəliş dövrəsi məcburidir. Son sual: «Peşəkar qrafik dizayner bunu portfoliosuna qoyardımı?» — əmin deyilsənsə, zəif hissəni tap.

## 10. Final export
```bash
python3 .claude/skills/ayra-creative-intelligence/scripts/grid_check.py out/A.png out/B.png ... --out final/grid_check.jpg
```
3:4 profil kəsimi + 150px kiçik nüsxə — kəsimdə mətn/üz itməməlidir. Postlar 1080×1350, Reels cover 1080×1920, PNG. Müştəri faylları `instagram-clients/<m>/` (gitignored); repoya müştəri adı/şəxsi məlumat düşmür.

## Təqdimat
İstifadəçiyə: yekun PNG-lər + grid preview + qısa hesabat (ideya, istifadə olunan referans prinsipi, real şəkil mənbəyi/lisenziyası, tənqid balları əvvəl→sonra, mütəxəssis təsdiqi tələb edən faktlar).

## Kompozisiya istiqamətləri (şablon deyil, kreativ yön — mövzuya görə seç)
Editorial magazine · art-directed photography · typographic poster · conceptual collage · minimal visual storytelling · object-led · portrait-led · educational infographic · modern campaign. «8 obyekt = 8 xanalı kataloq» avtomatizmi qadağandır: əvvəl daha güclü metafora axtar (məs. «10 oyun» → 0,00-lıq oyuncaq qəbzi; «hər şeyə yox» → böyüyən «Yox.» dialoqu).
Mənbə faylı: hər PNG ilə yanaşı redaktə edilə bilən `.html` (layer = element) `instagram-clients/<m>/<iş>/menbe/`-də saxlanır. Şrift yoxlaması: `ayra_design.py fontcheck <font> --text "ƏəİıŞşĞğÇçÖöÜü0123456789"`.

## Master brend faylı
Müştəri qovluğunda `MASTER_BRAND_FILE.md` varsa, hər işdən əvvəl ƏVVƏL o oxunur (mövqe, istiqamətlər, qadağalar, açıq suallar); `brand_profile.md` qərarlar jurnalıdır. Açıq sual olan mövzuda köhnə dəyər işlədilmir.
