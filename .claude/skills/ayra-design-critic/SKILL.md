---
name: ayra-design-critic
description: "Hazır dizaynı (cover, post, karusel, highlight, video kadrları, motion) müstəqil göz kimi tənqid edir — AI görünüşü, generic şablon hissi, tipoqrafiya, boşluq, brend uyğunluğu, Instagram grid və telefon oxunaqlığı. P0/P1/P2 tapıntılar və minimal düzəliş verir. İstifadə et: hər vizual nəticə istifadəçiyə göndərilməzdən ƏVVƏL, \"yoxla\", \"tənqid et\", \"review\", \"AI kimi görünür?\" deyiləndə."
---

# AYRA Design Critic

## Müstəqillik
Mümkünsə tənqidi **ayrı kontekstdə** apar (Agent alətilə yeni agent: ona yalnız faylları, brend vərəqini və direction.md-ni ver, dizaynerin öz izahını yox). Ayrı kontekst yoxdursa, hesabatda "öz-yoxlama" kimi qeyd et — müstəqil təsdiq iddia etmə.

## Müşahidə (faylları həqiqətən aç)
1. Tam ölçü (Read).
2. Telefon ölçüsü: 270 px enində kiçilt və bax.
3. Kontekst: profil gridində qonşu postlarla (3:4 kəsim) və ya highlight dairəsində.
4. Video üçün: kadr vərəqi (hər 1 s) + `qc_sheet.jpg`.

## Yoxlama siyahısı
**A. İlk 1 saniyə** — kim/nə görünür, mövzu nədir, niyə baxmalı? Bir cümlə ilə yaz; yaza bilmirsənsə P1.
**B. AI / şablon hissi** — simmetrik "mərkəz + gradient + parıltı", lazımsız şüşə/glow, hər yerdə eyni yumru künc, stok ikon yığını, mənasız bəzək, plastik dəri, səbəbsiz 3D. (`audit-ai-design-slop` meyarları)
**C. Tipoqrafiya** — böyük hərflərdə İ/I düzgünlüyü ("MİF", "İNKİŞAF"), iyerarxiya (≤3 səviyyə), sətir sınması (söz tək qalmır), aralıq, Ə/İ/Ş düzgün, kontrast (WCAG ≥4.5 kiçik mətn), kənardan ≥64 px.
**D. Kompozisiya** — bir fokus, nəfəs alan boşluq, optik mərkəz, ölçü ritmi, üz örtülmür, Instagram UI zonaları boşdur.
**E. Brend** — rənglər palitradan (`brand.py --check`), şrift brend şriftidir, müştərinin digər işləri ilə ailə kimi görünür, başqa müştəriyə bənzəmir.
**F. Həqiqət** — mətn faktı müştəri materialındadır, mənbə realdır, kadr manipulyasiya olunmayıb.
**G. Video/motion** — üz-qrafika örtülməsi, oxuma müddəti, keçid səbəbi, səs səviyyəsi, kəsilmiş cümlə.

## Hesabat
```
Nəticə: KEÇDİ / DÜZƏLİŞ / MÜŞAHİDƏ GÖZLƏYİR
Fayl + ölçü + müşahidə üsulu (tam / 270px / grid)
P0 (yalan, istifadə olunmaz) / P1 (aydın deyil, ciddi vizual qüsur) / P2 (cilalama) — hər biri: yer → problem → təsir → minimal düzəliş
```
P0/P1 bağlanmadan göndərmə. Düzəlişdən sonra yeni faylı yenidən aç. Ən çox 3 dövrə; həll olmayan "gözləyir" qalır.

## Əməkdaşlıq
Yoxlayır: `ayra-cover-designer`, `ayra-motion-director`, `ayra-ad-creative`. Köməkçi: `cover-independent-review`, `audit-ai-design-slop`, `audit-reference-originality`, `better-typography`, `better-colors`, `better-layout`, `webapp-testing`.
