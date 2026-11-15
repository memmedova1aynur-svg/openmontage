---
name: "ayra-professional-cover-designer"
description: "AYRA Professional Cover Design Engine V2 — Drive linki/videodan avtomatik premium Instagram Reels cover: portret seçimi, art direction (A jurnal / B ekspert portreti / C konseptual), editorial tipoqrafiya, HTML/CSS+SVG+Playwright render, 1080×1920 + 3:4 grid + 270 px yoxlaması, müstəqil estetik tənqid. Məndən referans/foto istəmədən işləyir. İstifadə et: 'cover', 'örtük', 'reels cover', 'thumbnail', 'post üz qabığı' deyiləndə və hər montaj təhvilində."
---

# AYRA Professional Cover Designer (Engine V2)

## Axın (hamısı məcburi)
1. **Workspace** — `ayra-studio-director` qaydası: müştəri, `editing-dna.md` → Cover bölməsi, `Approved Design Library` (`instagram-clients/<m>/approved/` və `_agency/approved_library.md`), bəyənilməyənlər siyahısı.
2. **Mövzu** — videonun transkriptindən əsas fikir, mif/fakt, hook; başlıq videonun öz sözlərindən (uydurma yox).
3. **Portret** — `ayra-smart-portrait-selector` (contact sheet → göz ilə seçim). Əvvəl rədd edilmiş kadrlar istisna.
4. **Art direction** — `ayra-design-director` 5 suala cavab: ən maraqlı vizual ideya, diqqət çəkən kompozisiya, uyğun portret/emosiya, brendi gücləndirən tipoqrafiya, gridə necə oturur.
5. **Üç fərqli istiqamət** (eyni şablonun rəng variantı DEYİL):
   - **A — Luxury editorial magazine**: `templates/ayra/v2/magazine.html` — studiya fonu, masthead (ekspertin adı) başın arxasında, issue sətri, cover-line-lar.
   - **B — Signature expert portrait**: `v2/signature.html` — krem səhifə, tağ pəncərədə portret, başlıq tağın kənarına yaxın, imza xətti (ad + rol).
   - **C — Conceptual**: `v2/concept.html` — vizual metafora (məs. mif xətlə pozulur, portret danışıq qabarcığında — "ağlamaq dildir"). Metafora videonun real fikrindən gəlir.
   Yeni konsept lazımdırsa yeni şablon yaz — eyni kompozisiyanı bütün müştərilərə tətbiq etmə.
6. **Tipoqrafiya** — `ayra-typography-specialist` (typecheck, `lang="az"`, şkala, sətir bölgüsü).
7. **Render** — `python3 .claude/skills/ayra-professional-cover-designer/render.py <şablon> <spec.json> <out.png>`; `data-check` xəbərdarlıqlarını düzəlt.
8. **Vizual QC** — özün bax: 1080×1920 tam, 3:4 mərkəz (y 240–1680), 270 px thumbnail, üzə yaxın zoom (yumşaqlıq, maska kənarı, retuş izi).
9. **ayra-visual-design-critic** (ayrı agent, estetika birinci) → P0/P1 düzəlt → yenidən render → müqayisə.
10. **Təhvil** — 3 ayrı PNG + yan-yana müqayisə (önizləmə). Təsdiqdən sonra prinsipləri workspace-ə və `_agency/approved_library.md`-yə yaz.

## QADAĞAN
Hər coverdə eyni şablon · portretin arxasına təsadüfi dairə · səbəbsiz iri rəngli düzbucaqlı blok · fotonun altına avtomatik ağ fade · təsadüfi gradient/parıltı/kölgə · Canva şablonu görünüşü · generic AI estetikası · kompozisiyanı pozan nəhəng başlıq · oxunmayan xırda mətn · uğursuz video screenshotu · bütün müştərilərə eyni üslub · veb-sayt kartı / dashboard görünüşü.
İşıq düşməsi yalnız fotoqrafik məntiqlə (studiya fonu), dən (grain) 5–7% overlay.

## Ölçülər və zonalar
1080×1920; profil gridi mərkəz 1080×1440 (y 240–1680) — başlıq və üz buradadır; Reels UI: alt 320 px, sağ 140 px boş qalır; kənar boşluğu ≥ 64–96 px.

## Fayllar
`templates/ayra/v2/*.html` (V2), `templates/ayra/*.html` (V1 — yalnız istinad), `_base.css` (Poppins yerli şriftləri), `render.py`.

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
