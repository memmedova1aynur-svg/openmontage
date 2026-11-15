---
name: dizayn-resurslari
description: "Agentliyin pulsuz dizayn resursları və yerli alətləri — şrift (Google Fonts, Fontshare, Fontsource + Azərbaycan hərfi yoxlaması), illüstrasiya/fon/naxış (unDraw, Open Doodles, Haikei, Hero Patterns, Poly Haven), açıq lisenziyalı foto (Openverse), hərəkət (GSAP, Anime.js, Lottie, Motion, Three.js, Remotion), yerli alətlər (Inkscape, Sharp, Fabric, Konva, ImageMagick, Blender, Playwright). İstifadə et: cover, post, karusel, highlight, video qrafikası üçün material, şrift, fon, tekstura və ya animasiya lazım olanda."
---

# Dizayn resursları (API açarsız)

İkonlar üçün ayrıca bacarıq var: `ikon-kitabxana`. Brend rəngi/şrifti: `musteri-brend`.
Alətlər yoxdursa: `bash .claude/skills/dizayn-resurslari/setup.sh`.

Bütün statuslar 15.11.2026-da bu mühitdən yoxlanılıb.

## Şriftlər

| mənbə | kodla | necə |
|---|---|---|
| Google Fonts | ✅ | `python3 .claude/skills/dizayn-resurslari/font.py "Playfair Display" 400,700` |
| Fontshare | ✅ | `font.py --fontshare satoshi 500,700` (API: api.fontshare.com/v2/fonts) |
| Fontsource | ✅ | api.fontsource.org/v1/fonts/<ad>, CDN cdn.jsdelivr.net/fontsource |
| Collletttivo, League of Moveable Type, Open Foundry | ✅ sayt | əl ilə seç, faylı endir, `font.py --yoxla` |
| Velvetyne | ↪ yönləndirir | brauzerdə |

**Qayda:** hər şrifti `font.py` ilə endir və ya `font.py --yoxla fayl.ttf` ilə yoxla — Ə Ğ İ ı Ş Ç Ö Ü tam olmalıdır.
Məsələn Satoshi (Fontshare) və DM Serif Display **Ə dəstəkləmir** → başlıqda işlətmə.

## İllüstrasiya, fon, naxış, tekstura

| mənbə | kodla | lisenziya / qeyd |
|---|---|---|
| unDraw | ✅ sayt | pulsuz, rəng dəyişir; API yoxdur, SVG-ni saytdan götür |
| Open Doodles, Open Peeps, Humaaans | ✅ | CC0 |
| Haikei | ✅ | SVG dalğa/forma generatoru (brauzerdə); sadə dalğanı özün SVG ilə yarada bilərsən |
| Hero Patterns | ✅ | CC BY 4.0, SVG naxışlar |
| Transparent Textures | ✅ | `https://www.transparenttextures.com/patterns/<ad>.png` (məs. cream-paper) |
| SVG Backgrounds | ✅ sayt | pulsuz versiya şərtlərini yoxla |
| Poly Haven | ✅ API | CC0 tekstura/HDRI/3D: `https://api.polyhaven.com/assets?t=textures&c=fabric` |

## Real foto və video (AI havası olmayan)

| mənbə | kodla | qeyd |
|---|---|---|
| Openverse | ✅ API (User-Agent `curl/8`) | `api.openverse.org/v1/images/?q=...&license_type=commercial` — hər nəticədə lisenziya var; `by`/`by-sa` müəllif adı tələb edir |
| Mixkit, Coverr | ✅ sayt | pulsuz video/musiqi; Mixkit montajda artıq işlənir |
| Mazwai | ↪ | brauzerdə |
| Pexels, Pixabay, Kaboompics | ❌ 403 | brauzerdə və ya API açarı ilə (açarı `request_credential` ilə istə, söhbətdə yox) |
| Unsplash | ↪ 307 | rəsmi API açar tələb edir |
| Wikimedia Commons | ⚠️ 429 | sorğu limiti; nadir hallarda |

**Qayda:** real insan fotosu yalnız lisenziyası aydın olanda; müştəri materialı həmişə üstündür.

## Hərəkət / animasiya (yerli, `/root/design-tools/node_modules`)

GSAP 3.15, Anime.js 4.5, Lottie Web 5.13, Motion 14.14, Three.js r187, Konva 10.9, Fabric 7.4, Sharp 0.35.
Video üçün əsas yol: **Remotion** (`remotion-best-practices`) + FFmpeg. HTML animasiyanı videoya: Playwright ilə kadr-kadr və ya HyperFrames.
LottieFiles, Lordicon, Rive: hər animasiyanın lisenziyasını ayrıca yoxla. Remotion: ≤3 nəfərlik şirkətə pulsuz, böyük komandaya lisenziya lazımdır.

## Yerli alətlər

| alət | nə üçün |
|---|---|
| Inkscape 1.2 | SVG → PNG/PDF, vektor redaktəsi (`inkscape in.svg -o out.png -w 1080`) |
| Sharp (Node) | foto + SVG kompozisiya, sürətli ölçü/format |
| Pillow (Python) | şəkil redaktəsi |
| Playwright | HTML/CSS dizaynı render və ekran görüntüsü (`webapp-testing`) |
| Fabric.js, Konva.js | laylı canvas kompozisiyası |
| ImageMagick 6.9 | format çevirmə, toplu emal |
| Blender 4.0 | 3D səhnə və render (CPU-da yavaş) |

## Cover iş axını (tövsiyə)

1. **Referans:** istifadəçidən və ya müştərinin bəyəndiyi işlərdən 2–3 nümunə — art direction təxminlə qurulmur.
2. **Brend:** `musteri-brend` → palitra, şrift.
3. **Material:** müştərinin real kadrı/fotosu > Openverse/Poly Haven > ikon (`ikon-kitabxana`).
4. **Kompozisiya:** HTML/CSS + SVG (şrift və boşluq nəzarəti ən dəqiqdir), Playwright ilə PNG.
5. **Yoxlama:** özün bax, `brand.py --check`, üz örtülmür, mətn kənara dirənmir.
