---
name: ikon-kitabxana
description: "Açarsız açıq ikon kitabxanaları (Iconify API vasitəsilə Phosphor, Lucide, Tabler, Heroicons, Iconoir, Remix, Material Symbols, Fluent Emoji, Simple Icons) — ikon axtarmaq, brend rəngində SVG/PNG yükləmək, seçim üçün önizləmə vərəqi çıxarmaq. İstifadə et: cover, highlight, karusel, video qrafikası üçün ikon lazım olanda; \"ikon\", \"icon\", \"Iconify\", \"Phosphor\", \"Lucide\" deyiləndə. İkonu əl ilə çəkmək əvəzinə əvvəl buradan götür."
---

# İkon kitabxanası (Iconify, API açarı lazım deyil)

İkonları kodla əl ilə çəkmə: dizaynerlərin çəkdiyi açıq dəstlərdən götür. Hamısı Iconify API ilə bir yerdədir
(280 kolleksiya, 550 mindən çox ikon). Alət: `.claude/skills/ikon-kitabxana/ikon.py`.

## Əmrlər

```bash
P=.claude/skills/ikon-kitabxana/ikon.py
python3 $P axtar "baby" --dest ph,tabler            # ad siyahısı
python3 $P onizle "breastfeeding" --reng "#DC5063" --fayl /scratch/onizle.png   # seçim vərəqi (özün bax)
python3 $P yukle ph:baby-duotone ph:heart-duotone --reng "#DC5063" --olcu 512 --png --qovluq out/
python3 $P lisenziya ph lucide fluent-emoji
```

Birbaşa link də işləyir: `https://api.iconify.design/ph/heart-duotone.svg?color=%23DC5063&height=512`

## Dəstlər və nə üçün

| prefiks | dəst | üslub | lisenziya |
|---|---|---|---|
| `ph` | Phosphor | 6 qalınlıq: thin, light, regular, bold, fill, **duotone** | MIT |
| `lucide` | Lucide | minimalist xətt | ISC |
| `tabler` | Tabler | peşəkar xətt, çox mövzu | MIT |
| `heroicons` | Heroicons | sadə, outline/solid | MIT |
| `iconoir` | Iconoir | zərif, incə | MIT |
| `ri` | Remix Icon | line/fill cütləri | Apache-2.0 |
| `material-symbols` | Google Material | ən geniş mövzu | Apache-2.0 |
| `fluent-emoji` / `fluent-emoji-flat` | Microsoft | rəngli emoji | MIT |
| `simple-icons` | brend loqoları | | CC0, amma loqo ticarət nişanıdır |
| `streamline` | Streamline | | CC-BY-4.0, müəllif adı yazılmalıdır |

SVG Repo kodla əlçatan deyil (serverdən 404); oradan yalnız brauzerdə, hər ikonun lisenziyasını yoxlayaraq.

## Qaydalar

- Bir seriyada **bir dəst və bir qalınlıq** işlət (məs. hamısı `ph:*-duotone`). Dəstləri qarışdırma.
- Rəngi müştərinin palitrasından ver (`musteri-brend` bacarığı → `brand.py <müştəri>`).
- Duotone ikonlarda ikinci ton ana rəngin 20% şəffaflığıdır; başqa ton lazımdırsa SVG-ni redaktə et.
- Əvvəl `onizle` ilə vərəq çıxar, özün bax, uyğun ikonları seç; istifadəçiyə seçim lazımdırsa vərəqi "önizləmə" adı ilə göstər.
- CC-BY dəstlərində müəllif adı tələbini istifadəçiyə bildir.
