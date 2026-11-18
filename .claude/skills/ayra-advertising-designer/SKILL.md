---
name: "ayra-advertising-designer"
description: "AYRA Advertising — reklam posteri, satış vizualı, tədbir/təlim/seminar afişası, kampaniya seriyası, xidmət təqdimatı (statik + animasiyalı). Tək mesaj, tək CTA, real məlumat; təsdiqlənməmiş tarix/qiymət [yer tutucu] kimi göstərilir. İstifadə et: 'reklam posteri', 'afişa', 'təlim reklamı', 'seminar', 'kampaniya vizualı', 'satış postu' deyiləndə."
---

# AYRA Advertising Designer

## Qaydalar
- Bir vizual = bir təklif = bir CTA. İyerarxiya: təklifin adı → kimə/nə üçün → kim aparır → tarix/format → əlaqə.
- Tarix, qiymət, yer, nəticə vədi YALNIZ müştəri təsdiqləyibsə; yoxsa `[Tarix]` və "Konsept nümunəsi" qeydi.
- Color blocking / bold typography istiqamətləri reklamda cəsarətli ola bilər; dekor yox — rəng blokunun funksiyası olmalıdır (iki zonanı ayırır).
- Portret blokun sərhədini keçə bilər (qatlı kompozisiya), mətn üzə və əllərə dəymir.
- Formatlar: post 1080×1350, story 1080×1920, A4/A3 çap PDF (`--size poster --fmt pdf`), motion versiya `ayra_design.py animate` (8–12 s, MP4 + GIF).

## İş axını
ayra-copywriter (mətn, hook) → ayra-design-director (istiqamət) → layout → render (png, pdf) → motion versiya (istəyə görə) → ayra-visual-design-critic → təqdim.

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
