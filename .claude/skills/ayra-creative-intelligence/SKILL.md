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

## Creative Intelligence v2 — araşdırma, ideya, art direction, yaddaş (16.11.2026)

### A. Multi-source research (mənbə → funksiya → alət; hamısı girişsiz və açarsız, real yoxlanılıb)
| Mənbə | Nə üçün | Alət / vəziyyət |
|---|---|---|
| Google | auditoriyanın sualları, yerli rəqiblər | `ayra-growth-strategist/scripts/research_suggest.py` (autocomplete) · Instagram indeksi: `WebSearch` + `allowed_domains=["instagram.com"]` (`site:` İŞLƏMİR) · **Google Trends: 429 — bloklanır** |
| YouTube | hook, struktur, izah metodu, kim nə danışır | `research_youtube.py` (görünən başlıq/baxış/tarix; şərhlər oxunmur) |
| Pinterest | vizual prinsip, kompozisiya, obyekt foto | `ayra-pinterest-research` |
| Behance | art direction, grid, tipoqrafiya, kampaniya sistemləri | `research_browser.py behance` (Playwright, girişsiz işləyir) |
| Meta Ad Library | sahədə reklam mesajları və təklif dili | `research_browser.py adslib --country AZ` (girişsiz işləyir; aktiv qalmaq ≠ uğur) |
| Ads of the World | kreativ reklam konseptləri | sayt açılır, axtarış səhifəsi zaman aşımı — `WebSearch` ilə |
| Elm | faktın özü (caption üçün yox, fikir üçün) | WHO/CDC/AAP/ABM/NAEYC səhifələri; PubMed `eutils` API işləyir; **Google Scholar yönləndirir/bloklanır** |
Hər tapıntı: mənbə linki + tarix + işarə: **FAKT** (mənbə ilə) · **MÜŞAHİDƏ** (araşdırmada görünən) · **HİPOTEZ** (kreativ ehtimal) · **TEST** (paylaşıb ölçüləcək). Autocomplete ≠ axtarış həcmi; Pinterest populyarlığı ≠ Instagram uğuru; YouTube baxışı ≠ Instagram zəmanəti. Məqsəd link yığmaq deyil — dövrün sonunda 8 nəticə: real problemlər · cavabsız suallar · təkrarlanan standart mövzular · ehtimal boşluqlar · ekspert rakursları · vizual ideyalar · format imkanları · fərqlənmə istiqaməti.

### B. Creative Idea Engine (dizayndan ƏVVƏL, hər mövzu üçün `brief.md`)
1 **Audience insight** (real problem/hiss/yanlış inanc, bir cümlə) → 2 **Strateji məqsəd** (yeni auditoriya · ekspert imici · etibar · yadda saxlanma · paylaşma · xidmətə maraq · yeni seqment) → 3 **Big idea**: daxildə ən az 3 rakurs düşün (gündəlik situasiya · vizual metafora · ekspert müşahidəsi · gözlənilməz sual · nümayiş · müqayisə · mini hekayə · tanınan səhnə), ən güclüsünü ÖZÜN seç və bir cümlə ilə səbəbini yaz — istifadəçiyə 3 variant təqdim etmə; digər ikisi `idea_bank.md`-yə → 4 **Hook** (məzmuna sadiq; qorxu, manipulyasiya, AI konstruksiyaları yox) → 5 **Treatment** (talking head · nümayiş · obyektlə izah · vizual müqayisə · sual-cavab · editorial karusel · infoqrafika · mini hekayə · situasiya). Ardıcıl iki kontent eyni treatment-də olmur.

### C. Cross-industry art direction
İlham yalnız müştərinin sahəsindən deyil: moda jurnalı (nəhəng kəsilmiş başlıq, boşluq, səhifə ritmi) · premium kosmetika still life (tək obyekt + monoxrom rəng sahəsi + sərt təbii kölgə + xammal yanında) · muzey/sərgi posteri (tipoqrafik sistem, təkrar, rəng bloku) · kitab/jurnal · təhsil brendləri · interyer · qida reklamı · sənədli film qrafikası · infoqrafika. Kopyalanmır — prinsip götürülür və müştərinin dünyasına çevrilir.
**Art direction brief** (hər kontent): əsas vizual fikir · kompozisiya · palitra · tipoqrafik iyerarxiya · foto/obyekt · işıq və atmosfer · fokus · mətn yeri · grid görünüşü · mobil oxunaqlılıq. Gündəlik obyekt (ayaqqabı, stəkan, düymə, qaşıq, kitab) metafora ola bilər — mövzu ilə əlaqəsi aydın olmalı, dekorativ obyekt yox.

### D. Vizual material — üç ayrı kateqoriya
`references/` (Pinterest/Behance — yalnız referans, yekun dizayna girmir) · `assets/ayra-library/` (lisenziyalı stok, metadata ilə) · `instagram-clients/<m>/raw|assets` (müştərinin öz foto/videosu — üstünlük). Seçim meyarı: keyfiyyət · işıq · kompozisiya · mövzu · brend rəngi · fon · forma · estetika · crop · lisenziya. Zəif material dizaynı «tamamlamaq» üçün işlədilmir — alternativ kompozisiya seçilir.

### E. Creative memory (müştəri başına, qarışmır)
`instagram-clients/<m>/creative-library.md`: təsdiqlənmiş işlər · bəyənilmiş Figma frame-ləri · rədd edilənlər + səbəb · tipoqrafiya · karusel strukturları · foto kompozisiyaları · metaforalar · montaj yanaşmaları · işləyən hook strukturları · reklam ideyaları — hər birində «niyə güclüdür / hansı prinsipi öyrədir». Hər təsdiq/düzəlişdən sonra yenilənir. Agentlik səviyyəli ümumi prinsiplər: `templates/ayra/taste/TASTE_LIBRARY.md`.

### F. Creative Review Board (final təqdimdən əvvəl, müstəqil Agent)
4 baxış: **Brand manager** (mövqeyə xidmət edir?) · **Creative director** (fərqli və yadda qalan?) · **Designer/editor** (iyerarxiya, kompozisiya, foto, montaj, icra) · **Auditoriya + mövzu eksperti** (niyə baxsın? faydalı, aydın, etibarlı?). Meyarlar: ilk baxışda dayandırma · ideya · brend · ekspert etibarı · vizual keyfiyyət · oxunaqlılıq · dəyər · grid. Render/Figma screenshot üzərində; kod işləməsi keyfiyyət deyil; özünə yüksək bal yox; standartdan aşağı nəticə final kimi təqdim edilmir.

### G. Strategy before quantity
Say istehsal hədəfidir, strategiya deyil. Zəif mövzu daha güclüsü ilə əvəz olunur. Paket bütöv qiymətləndirilir: «Bu 15 paylaşım brendi hansı istiqamətə aparır? 15 gündən sonra auditoriya bu mütəxəssis haqqında hansı yeni fikrə sahib olacaq?» — cavab planın sonunda yazılır.

### H. Performance learning loop
İstifadəçi Insights ekran görüntüsü/rəqəm verəndə: baxış · izləmə müddəti · saxlama · paylaşma · şərh · profil ziyarəti · yeni izləyici · müraciət → `instagram-clients/<m>/analytics/insights.csv` (ID ilə). Hər kontent öz məqsədinə görə qiymətləndirilir (diqqət ≠ etibar ≠ satış; yüksək baxış satış demək deyil). Növbəti dövrün bölgüsü, format və hook seçimi buna görə dəyişir. Məlumat yoxdursa — «yoxdur» yazılır, statistika uydurulmur.

## Viral Content & Humor Intelligence (universal modul; müştəri faktları ayrı faylda)
Mizah brendin əsas xətti deyil — müştərinin master faylında icazə verilən tezlikdə (məs. 15 paylaşımda ≤1) və yalnız güclü ideya strateji məqsədə xidmət edəndə. Kvota üçün mizah posti yaradılmır.
**Hədəf qaydası:** zarafat situasiyaya, stereotipə, absurd gözləntiyə, yanlış inanca yönəlir — uşağa, valideynin çətinliyinə, müəllimin şəxsiyyətinə yox. Təhlükəli davranış tövsiyə kimi oxuna bilməz (absurd həddə qədər şişirdilir); həssas mövzular (uşaq təhlükəsizliyi, inkişaf fərqlilikləri, əmizdirmə çətinliyi, doğuş sonrası psixi vəziyyət) xüsusi ehtiyatla və mütəxəssis təsdiqi ilə.

| Növ | Mexanizm | IG formatı | Risk |
|---|---|---|---|
| Absurd | məntiqi sonuna qədər aparılmış gözlənilməzlik | illüstrasiyalı karusel | aşağı (absurd = tövsiyə deyil) |
| Deadpan | gülməli məzmun tam ciddi formada | təlimat, sənəd, rəsmi cədvəl | aşağı |
| Vizual ironiya | şəkil ↔ mətn ziddiyyəti | tək kadr, cover | aşağı |
| Relatable | izləyici öz həyatını görür | POV, tarixçə, siyahı | aşağı |
| Satira | köhnəlmiş fikrin tənqidi | saxta proqram, «akademiya» | orta — hədəf inanc, şəxs yox |
| Şişirtmə | gündəlik hadisə böyüdülür | komiks, karusel | aşağı |
| Gözlənti vs reallıq | iki kadr kontrastı | split karusel | aşağı |
| Parodiya | tanış format (reklam, təlimat, xəbər) | saxta reklam, manual | aşağı–orta (brend adı yox) |
| Müşahidə | görünməyən gündəlik detal | vaxt damğası, siyahı | aşağı |
| Lokal | dil, ailə mədəniyyəti, məişət | hər format | orta — region/qrup ələ salınmır |
| Situasiya komediyası | konkret səhnənin özü | mini səhnə Reels | aşağı |
| Özünə ironiya | öz təcrübəsinə gülmək | ekspertin öz «səhvləri» | aşağı, amma ekspert etibarını azaltmamalı |
| Cəsarətli (edgy) | sərhəddə təəccüb | — | **yüksək** — ekspert brendlərində yalnız ayrıca təsdiqlə |
| Rol dəyişmə | rollar yer dəyişir | «uşağın müqaviləsi» | aşağı–orta |
| Mockumentary | sənədli film dili + komik məzmun | CCTV, səsli izah | aşağı |

**Viral Creative Lab — hər ideya üçün 10 bənd:** mövzu və problem · konsept · hook (1-ci slayd/ilk saniyə) · mizah mexanizmi · niyə göndəriləcək · ehtimal olunan şərhlər (PROQNOZ kimi işarələnir) · ekspert mövqeyinə xidməti · art direction · reputasiya riski · məqsəd + ölçü göstəricisi. Formatlar: karikatura, komiks, mini sənədli, saxta reklam, situasiya, interaktiv karusel, metafora, müqayisə, POV, real şərhə cavab, illüstrasiyalı hekayə, sosial eksperiment, ekspertin yumorla izahı. Viral potensial zəif/brendə uyğun olmayan ideyanı keçirmir.
**Ekspert körpüsü:** viral postun ardınca eyni mövzuda ekspert Reels/karusel + caption-da yönləndirmə — diqqət profil ziyarəti və izləyiciyə çevrilsin.
**Comment Intelligence:** real şərhlər (ekran görüntüsü/mətn) ayrıca mənbədir: davam etdirilən zarafat, lokal ifadələr, auditoriyanın əlavə etdiyi obrazlar, yeni ideya, həqiqi maraq vs əyləncə. Real şərh ↔ proqnoz şərh heç vaxt qarışdırılmır.
**Ölçmə (məqsədə görə):** tanınma — görüntüləmə, əhatə, göndərilmə/əhatə, repost · ekspertlik — saxlama, məzmunlu şərh, profil ziyarəti, izləyici/ziyarət · xidmət — real müraciət (varsa). Yüksək baxış satış uğuru deyil. Hər yeni nəticə müştərinin case study-ləri ilə müqayisə olunur.
**Araşdırma mənbələri (yoxlanılıb 16.11.2026):** TikTok Creative Center açılır (ölkə seçimi məhduddur) · Reddit: birbaşa 403, axtarış alətində bloklanır — əlçatmaz · Google Trends 429 — əlçatmaz · digərləri §A cədvəlində. AZ/TR/EN araşdırılır; xarici zarafat tərcümə edilmir və rəqib postu kopyalanmır — mexanizm götürülüb yerli situasiyaya çevrilir.
