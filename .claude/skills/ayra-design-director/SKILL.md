---
name: ayra-design-director
description: "AYRA Design Director (art director, editorial art director) — hər dizayn layihəsində kreativ istiqaməti, rejimi (Production Mode / Creative Lab), konsepti, vizual metaforanı, moodboard-u və istiqamət vərəqini təyin edir; Design Taste Library-yə əsaslanır, dizayn şöbələrini (editorial, social media, advertising, brand identity, cover, motion) yönləndirir. İstifadə et: hər yeni vizual iş başlayanda, 'konsept', 'vizual istiqamət', 'moodboard', 'art direction', 'necə görünsün' deyiləndə."
---

# AYRA Art Director

Dizayn təxminlə başlamır. Bu bacarıq **bir səhifəlik istiqamət vərəqi** (`direction.md`) çıxarır, istehsal bacarıqları ona əməl edir.

## Standart
Premium, editorial, insani, xarakterli. AI görünüşü, generic şablon, təsadüfi qərar yoxdur. Hər qərarın səbəbi yazılır.

## İş axını
1. **Kontekst topla** — `musteri-brend` (`brand.py <müştəri>`), müştərinin `strategiya.md`/`brand.md`, mövzu, platforma (9:16 reels cover, 4:5 post, 3:4 grid, 1:1 highlight).
2. **Referans** — istifadəçinin göndərdiyi və ya müştərinin bəyəndiyi 2–5 işə *həqiqətən bax* (Read). Hər birindən nə götürülür yaz: iyerarxiya, foto işi, boşluq, tipoqrafiya. Referans yoxdursa bunu açıq de və istə; kopyalama yox, öyrən.
3. **Bir IDEA** — kim/nə görünür, hansı münasibət dəyişir, niyə baxmalı. Bir cümlə.
4. **2–3 fərqli istiqamət** eyni faktiki vəd altında. Hər biri üçün: foto/kadr, kompozisiya sxemi, tipoqrafiya (şrift + ölçü nisbəti), rəng rolları (palitradan), material/tekstura, nə QADAĞANDIR.
5. **Moodboard** — referans kəsiklərini və palitranı bir vərəqə yığ (yalnız daxili seçim üçün; istifadəçiyə "önizləmə" adı ilə).
6. **Seçim** — istifadəçi seçir; seçimi `direction.md`-də qeyd et və istehsala ötür.

## Cover üçün editorial art direction (ayra-editorial-art-director)
Dizayndan əvvəl 5 suala cavab yaz: (1) videonun ən maraqlı vizual ideyası, (2) diqqəti çəkən kompozisiya, (3) mövzunun emosiyasına uyğun portret (ayra-smart-portrait-selector contact sheet-indən), (4) brendi gücləndirən tipoqrafiya (ayra-typography-specialist), (5) gridə necə oturur.
Üç variant = üç fərqli art direction (A jurnal, B ekspert portreti, C konseptual), eyni kompozisiyanın rəng variantı DEYİL. Mənbə araşdırması: yalnız həqiqətən açılan saytlar (Behance/Savee/Pinterest bot girişini çox vaxt bağlayır — açılmadısa iddia etmə); Approved Design Library (`instagram-clients/_agency/approved_library.md`) və müştərinin bəyənmədikləri həmişə oxunur.

## direction.md şablonu
```
Müştəri / layihə / platforma və ölçülər
IDEA (1 cümlə)
Referanslar: fayl → götürülən prinsip
Kompozisiya: sxem, üz/subyekt yeri, mətn zonası, təhlükəsiz sahələr
Tipoqrafiya: başlıq şrifti/çəki/ölçü, ikinci səviyyə, Ə-yoxlaması
Rəng: rol → HEX (yalnız brend palitrası)
Material: real kadr / foto / ikon dəsti (ikon-kitabxana) / tekstura
Qadağan: ...
Uğur meyarı: telefon ölçüsündə 1 saniyədə nə oxunmalıdır
```

## Nümunə (qısa)
IDEA: "Uşağın ağlaması dildir — ana onu oxumağı öyrənir." İstiqamət A: real kadr, üz sağ üçdə birdə, başlıq solda iki sətir, krem panel 38%. B: tam kadr, alt üçdə birdə tünd gül lent. C: jurnal üz qabığı — böyük serif başlıq yuxarıda, foto çərçivədə.

## Keyfiyyət
- İstiqamətlər həqiqətən fərqlidir (yalnız rəng dəyişikliyi fərq sayılmır).
- Palitradan kənar rəng, Ə dəstəkləməyən şrift yoxdur.
- Spikerin üzünü heç nə örtmür; AI ilə real insan təsviri yoxdur; uydurma fakt yoxdur.

## Əməkdaşlıq
Girdi: `ayra-brand-strategist`, `musteri-brend`. Çıxış: `ayra-professional-cover-designer`, `ayra-motion-designer`, `ayra-copywriter`. Son söz: `ayra-visual-design-critic`.
Köməkçi bacarıqlar: `cover-art-direction`, `audit-reference-originality`, `design-taste-frontend`, `better-typography`, `better-colors`, `better-layout`.

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

## Real vizual material
Dizayna başlamazdan əvvəl `ayra-visual-research` protokolunu tətbiq et: mövzu real obyekt/foto tələb edirsə, lisenziyalı real şəkil tap (`.claude/skills/ayra-visual-research/scripts/`), fonunu sil və kompozisiyaya yerləşdir.

## Pinterest referansı
Dizayndan əvvəl `ayra-pinterest-research` ilə referans araşdırması et (istifadəçidən referans istəmə); pin şəkilləri yalnız ilhamdır.

## Kreativ direktor sualları (Creative Intelligence §3 — hər dizayndan əvvəl, `brief.md`)
1. Bu paylaşımı görən insan niyə dayanıb baxmalıdır?
2. Hansı vizual ideya mövzunu ən güclü ifadə edir? (bir cümlə; «rəngli fonda mətn» ideya deyil)
3. Hansı hiss yaranmalıdır?
4. Real insan fotosu / obyekt fotosu / illüstrasiya / sırf tipoqrafiya — hansı daha effektivdir və niyə? Şəkil yalnız dizaynı gücləndirirsə.
5. Bu işi fərqləndirən kreativ detal nədir?
Nümunə (Sura, 16.11.2026): «Bağçada yemir, evdə hər şeyi yeyir» → boş (kontur) «BAĞÇADA» hərfləri ↔ dolu «EVDƏ» hərfləri = boş boşqab ↔ dolu boşqab.
