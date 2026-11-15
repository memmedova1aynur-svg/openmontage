---
name: ayra-typography-specialist
description: "AYRA tipoqrafiya mütəxəssisi — şrift seçimi və cütləşdirmə, tipoqrafik şkala, sətir bölgüsü, kerning/tracking, Azərbaycan əlifbasının (Ə ə İ ı Ş ş Ğ ğ Ç ç Ö ö Ü ü) dəstəyi və böyük-hərf çevrilməsi yoxlaması. İstifadə et: hər cover/karusel/motion mətni qurulanda, 'şrift', 'tipoqrafiya', 'başlıq ölçüsü', 'hərf' deyiləndə."
---

# AYRA Typography Specialist

## Alət
```bash
python3 .claude/skills/ayra-typography-specialist/typecheck.py <font.ttf> [--text "Başlıq mətni"]
```
Yoxlayır: 14 Azərbaycan hərfinin glyph-i, `İ/ı` böyük-kiçik cütləri, mətndə dəstəklənməyən simvol. Şrift endirmək: `dizayn-resurslari/font.py`.

## Qaydalar
- **Brend şrifti əsasdır** (brand_kit `profile.fonts`). Yeni ailə əlavə etmək = vizual kimlik dəyişikliyi → istifadəçi təsdiqi.
- **İyerarxiya**: ən çox 3 səviyyə. Şkala nisbəti 1.25–1.5 (məs. 24 / 36 / 96). Başlıq/alt mətn ölçü fərqi ən az 2.5×.
- **Sətir bölgüsü**: mənaya görə böl ("Ağlasın, / ciyərləri / açılsın?"), tək söz sətirdə qalmasın (dul/yetim), bağlayıcı sətir sonunda qalmasın.
- **Aralıq**: başlıq line-height 0.95–1.05, tracking −2…−3% (60 px+); böyük hərfli kicker tracking +18…+24%; mətn 1.3–1.45.
- **Vurğu**: bir üsul — ya rəng, ya kursiv/çəki; ikisi birlikdə yox.
- **Azərbaycan dili**: HTML-də `<html lang="az">` MƏCBURİ (əks halda `text-transform:uppercase` "i"-ni "I" edir). Python/PIL-də `.upper()` işlətmə — `az_upper()` (`i→İ`, `ı→I`) istifadə et.
- **Mobil**: 270 px enində başlıq oxunmalı; ən kiçik mətn 1080 px kətanda ≥ 24 px; kontrast kiçik mətndə ≥ 4.5:1.
- **Optik**: böyük başlıqda sol kənarı optik düzləndir (A, V, " kimi hərflər 2–6 px kənara çəkilir).

## Çıxış
`direction.md`-yə tipoqrafiya bloku: ailə/çəki, ölçülər, line-height, tracking, sətir bölgüsü, vurğu üsulu, typecheck nəticəsi.

## Əməkdaşlıq
ayra-art-director-dan istiqamət alır, ayra-professional-cover-designer / ayra-design-studio / ayra-subtitle-designer / ayra-motion-designer-ə şkala verir. Köməkçi: better-typography, musteri-brend, dizayn-resurslari.
