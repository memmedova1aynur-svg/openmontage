---
name: "ayra-editorial-designer"
description: "AYRA Editorial — jurnal üz qabığı, editorial poster, müsahibə dizaynı, premium şəxsi brend vizualları, foto+tipoqrafiya kompozisiyaları, lüğət/ensiklopediya kimi konseptual tipoqrafik formalar. Real portret + editorial qrid + serif/sans cütü. İstifadə et: 'jurnal', 'editorial', 'müsahibə', 'premium portret vizualı', 'magazine cover' deyiləndə və ekspert mövqeyini gücləndirən cover lazım olanda."
---

# AYRA Editorial Designer

## Prinsiplər (TASTE_LIBRARY.md → Editorial, Luxury Editorial, Documentary Editorial, Swiss)
- Qrid: 1080 enində 88–96 px kənar, 12 sütun; mətn bloku 4–5 sütun, foto 6–8 sütun və ya full-bleed.
- Ölçü kontrastı: başlıq/mətn ≥ 5:1 (məs. 236 / 40). Bir nəhəng söz + kiçik, sakit mətn.
- Foto: ya cəsarətli böyük (üz 30–40% en), ya kiçik sənədli detal (əllər, əşya) — orta ölçülü "pasport şəkli" yox.
- Serif (Newsreader/Fraunces) editorial səs, sans (Schibsted Grotesk/Poppins) məlumat səsi. Ə yoxlaması məcburi.
- Konseptual forma: lüğət maddəsi, indeks, jurnal sətri, sitat, rəqəm — mövzunun real fikrindən.
- Mif/fakt kimi qarşıdurmalar tipoqrafiya ilə (üstündən xətt, rəng tonu), dekorla yox.

## Alətlər
`ayra_design.py render|preview|grid`, ayra-smart-portrait-selector, ayra-photo-retouch, ayra-typography-specialist.

## İş axını
Brif (auditoriya, emosiya, əsas mesaj, niyə diqqət etsin, brend xarakteri) → istiqamət (taste kataloqundan) → portret/foto → kompozisiya (HTML) → render → preview (tam/3:4/270) → ayra-visual-design-critic (ən çox 2 düzəliş dövrü) → təqdim.

## Nümunə
"Körpənin dili" (Creative Lab test): lüğət maddəsi `ağlamaq [ağ·la·maq] fel — 1. Körpənin bizə nəsə izah etmək üçün istifadə etdiyi dil. bax: mif — ~~«ağlasın, ciyərləri açılsın»~~` + sağ-alt sənədli portret.

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
