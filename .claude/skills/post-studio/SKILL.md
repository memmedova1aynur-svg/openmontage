---
name: post-studio
description: Instagram post, karusel və qısa animasiyalı video (4:5 / 9:16) hazırlamaq üçün sürətli istehsal xətti — HTML şablon, Playwright render, kadr-kadr video, SFX + -14 LUFS səs, telefon ölçüsündə yoxlama və Impeccable detektoru. "post hazırla", "karusel", "hərəkətli post", "video post", "render et", "4:5", "Reels üçün 9:16" deyiləndə və ya hər hansı brend vizualı istehsal ediləndə işlət.
---

# Post Studio

Bir posta 6 addım. Hər addımın skripti `scripts/` qovluğundadır; əl ilə Playwright/ffmpeg kodu yazma.

## 1. Brif və rol
- Əvvəl `marketinq-sistemi` skill-i ilə müştərini müəyyən et və `instagram-clients/<müştəri>/brand.md` qaydalarını oxu (rənglər, şriftlər, qadağalar oradan gəlir).
- Postun rolunu seç (brand.md-də başqa sistem yoxdursa): Güldürür · Öyrədir · Göstərir · Analiz edir · Pərdə arxası · Fikir bildirir · Danışdırır (satışda + Təklif edir). Eyni rol ard-arda gəlməsin.

## 2. HTML
- Bir HTML faylı = bir post. Karusel üçün bir fayl, slaydlar `#s1 #s2 ...` hash-ı ilə (`const P={}; P.s1=()=>{...}; P[location.hash.slice(1)]()`).
- `body` ölçüsü: post 1080x1350, Reels/story 1080x1920. Fontlar Google Fonts-dan (`display=block`), sonda `document.fonts.ready.then(()=>document.title='done')`.
- **Animasiya üçün**: `window.TIMES={TOTAL:san}` və `window.renderFrame=t=>{...}` — hər şey yalnız `t`-dən hesablanır (CSS animation/transition yox), ona görə kadrlar deterministikdir.

## 3. Render
```bash
node .claude/skills/post-studio/scripts/shoot.js post.html out/ s1 s2 s3      # statik / karusel
node .claude/skills/post-studio/scripts/vshoot.js video.html frames/          # video kadrları (30 fps)
python3 .claude/skills/post-studio/scripts/encode.py --frames frames/ --out v.mp4 --total 10 \
  --sfx '[["pop",1.0,-22],["swoosh",2.0,-26],["ding",5.6,-18]]'              # səs + MP4 + QA
```
SFX: `pop` (klik/kart), `swoosh` (keçid), `ding` (final). Səviyyə -18…-30 dB; musiqi lazımdırsa ayrıca əlavə et.

## 4. Yoxla (göndərmədən əvvəl, bir baxışda hamısı)
- `sh scripts/phone_check.sh out/s1.png` → 390px önizləməyə bax. **1080 endə heç bir yazı 24px-dən kiçik olmasın**; imza oxunaqlı olsun.
- `.claude/skills/impeccable/scripts/impeccable detect --json post.html` — real problemləri düzəlt (kontrast, kəsilmə); statik qrafikada yanlış siqnalları (dəftər xətləri, kənara çatan zolaqlar) qeyd et.
- Videoda 2-3 kadra bax (`phone_check.sh v.mp4 5`): üst-üstə düşmə, kəsilən söz, boş kadr, sayğac/rəqəm məntiqi.
- Reels 9:16-da mətn təhlükəsiz zonada: yuxarıdan 220px, aşağıdan 380px boş.

## 5. Təhvil
- Faylları **tək-tək** göndər (SendUserFile, display: render). Zip göndərmə.
- Karusel slaydlarını sıra ilə bir çağırışda göndər.
- Caption: müştərinin brand.md üslubunda; klişe sual yox (şəkildə sual varsa, caption-da olmasın).

## 6. Yaddaş
Təhvildən sonra müştərinin `context.md` (və ya `master_context.md`) faylına bir sətir: tarix, post adı, fayl yolu, verilən rəy.

## Ev qaydaları (hamı üçün)
- Fakt, rəqəm, statistika uydurma; real şirkət loqosu və brend dizaynını təqlid etmə (yalnız adla analiz).
- Dini simvollar və dini mövzular üzərində zarafat yox.
- Real insan üzü: yalnız razılıqla; stok foto CC0/PD olsun, mənbəni qeyd et.
- Müştərini lağa qoyan yumor yox — insanlar özünü tanısın, incimsin yox.
