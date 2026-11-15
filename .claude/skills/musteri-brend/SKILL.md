---
name: musteri-brend
description: Hər müştərinin brend rənglərini, şriftlərini və vizual qaydalarını istənilən dizayna (cover, highlight, karusel, post, video qrafikası, PDF) sistemli tətbiq edir. Anthropic-in "brand-guidelines" bacarığının agentlik üçün fərdiləşdirilmiş versiyası. İstifadə et: müştəri üçün hər hansı vizual hazırlananda, "brend rəngləri", "brend kit", "şrift", "onun üslubunda", "filan müştəri üçün dizayn" deyiləndə.
---

# Müştəri brend qaydaları

Anthropic-in `brand-guidelines` bacarığı bir brendin (Anthropic) rəng və şriftlərini sabit yazır.
Bu versiya eyni işi **hər müştəri üçün ayrıca** edir: brend məlumatı koda yazılmır, müştərinin
gizli qovluğundan oxunur (`instagram-clients/<müştəri>/`, repoya düşmür).

## 1. Əvvəlcə oxu

```bash
python3 .claude/skills/musteri-brend/brand.py <müştəri-qovluğu>
```

Bu çap edir: palitra (rol → HEX), şriftlər və onların Azərbaycan hərflərini (Ə Ğ İ Ş Ç Ö Ü) dəstəkləyib-dəstəkləmədiyi,
təsdiq vəziyyəti, qeydlər. Mənbələr: `brand_kit.json` (əsas), `brand.md`, `strategiya.md`, `voice.md` (varsa).

Müştəri bəlli deyilsə — soruş. Bir müştərinin rəngini, şriftini, mətnini heç vaxt başqasına daşıma.

## 2. Rəng rolları (bütün müştərilər üçün eyni açarlar)

| açar | rol |
|---|---|
| `acc` | əsas vurğu: başlıq, düymə, lent |
| `ink` | ən tünd ton: əsas mətn, vurğu sözü |
| `acc2` | yumşaq vurğu: örtük fonu, altyazı vurğu bloku |
| `rose` / `bg2` / `bg3` | köməkçi tonlar: forma, ikinci plan |
| `paper` | ən açıq fon |
| `paper2` | ikinci açıq fon, kart |
| `txt` | tünd fon üstündə mətn |
| `bg` | tünd/rəngli fon |

Qaydalar:
- Palitradan kənar rəng işlətmə. Ara ton lazımdırsa, mövcud iki rəngin qarışığı və ya şəffaflığı ilə al.
- Mətn kontrastı: açıq fonda `ink`, rəngli fonda `txt`. Kiçik mətni heç vaxt `acc2`/`paper2` fonunda `acc2` tonunda yazma.
- `forbiddenColors` siyahısındakı rəngləri işlətmə.
- `paletteApproved: false` olarsa nəticəni "qaralama" kimi təqdim et, müştəri təsdiqini gözlə.

## 3. Şrift

- `profile.fonts.head` başlıq, `body` mətn, `accent` (varsa) əl yazısı/vurğu üçün.
- Şrift faylı yoxdursa Google Fonts-dan endir (User-Agent "Mozilla/4.0" TTF qaytarır), sonra `brand.py` ilə Ə dəstəyini yoxla.
- Ə dəstəkləməyən şrift işlətmə (məsələn DM Serif Display). Əvəzinə eyni xarakterli, Ə dəstəkləyən şrift seç və bunu bildir.

## 4. Vizual qaydalar (agentlik, hamı üçün)

- Spikerin üzünü heç nə örtmür (yarımşəffaf rəng də).
- Real insanların AI ilə yaradılmış təsviri yoxdur.
- Uydurma fakt, rəqəm, qiymət yoxdur; real başlıq və sitatlar müştərinin öz videosundan/mətnindən götürülür.
- Kollaj yox: hər fayl ayrıca göndərilir (seçim üçün önizləmə istisnadır və belə adlanır).
- Müştəriyə xas qaydalar: `brand_kit.json → rules`, `instagram-clients/_agency/qaydalar.json` və `strategiya.md`.

## 5. Yoxlama (göndərmədən əvvəl)

1. Şəkildəki bütün rənglər palitradadırmı? (`brand.py <müştəri> --check şəkil.png` ən çox işlənən rəngləri palitra ilə müqayisə edir)
2. Şriftlər brend şriftləridirmi, Ə/İ/Ş düzgün çıxırmı?
3. Mətn kənara dirənmir, üst-üstə düşmür?
4. Instagram kəsimi: highlight dairəvi, grid 3:4, post 4:5 — vacib element kəsilmir?
5. Nəticəyə özün bax (Read) və yalnız sonra göndər.

## 6. Yeni müştəri / dəyişiklik

Yeni müştəri: `instagram-clients/_template/` kopyala, `brand_kit.json`-u doldur.
Müştəri yeni rəng/şrift təsdiqləyəndə `brand_kit.json`-u yenilə, `paletteApproved: true` et və `profile.paletteNote`-a tarix + mənbə yaz.
