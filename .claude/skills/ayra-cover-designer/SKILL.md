---
name: ayra-cover-designer
description: "Premium Instagram reels cover, post, karusel və highlight örtükləri hazırlayır — müştərinin real kadrları/fotoları və brend kimliyi ilə, HTML/CSS + SVG + Playwright ilə dəqiq tipoqrafiya. İstifadə et: \"cover\", \"örtük\", \"reels cover\", \"karusel cover\", \"highlight\", \"post dizaynı\" deyiləndə. Əvvəl ayra-art-director istiqaməti, sonra ayra-design-critic yoxlaması."
---

# AYRA Cover Designer

## Prinsip
Real material + dəqiq tipoqrafiya + brend sistemi. Cover = ayrıca dizayn işi, videonun təsadüfi kadrı deyil.

## İş axını
1. `direction.md` oxu (yoxdursa `ayra-art-director` ilə qur). Brend: `python3 .claude/skills/musteri-brend/brand.py <müştəri>`.
2. **Kadr seçimi** — videodan bir neçə namizəd kadr çıxar (`ffmpeg -ss T -i v.mov -frames:v 1`), göz açıq, ağız neytral/təbəssüm, kəskin kadrı seç. Üzü `templates/expert-reels/pro/facedet.py` ilə tap. Kadrı süni intellektlə dəyişdirmə; yalnız rəng/işıq düzəlişi.
3. **Kompozisiya HTML-də** — `templates/ayra/cover.html` şablonundan başla (CSS dəyişənləri: palitra, şrift, üz qutusu). Şriftləri `@font-face` ilə yerli TTF-dən yüklə (`dizayn-resurslari/font.py`).
4. **Render** — `python3 .claude/skills/ayra-cover-designer/render.py cover.html out.png --w 1080 --h 1920` (Playwright + /opt/pw-browsers/chromium).
5. **Özün bax** (Read) telefon ölçüsündə (270 px enində) və tam ölçüdə. Grid kəsimi (3:4 mərkəz) üçün ayrıca önizləmə.
6. **Brend yoxlaması** — `brand.py <müştəri> --check out.png`.
7. `ayra-design-critic`-ə ötür; P0/P1 düzəlməmiş göndərmə.

## Ölçülər
- Reels cover 1080×1920, amma profil gridində 1080×1440 (3:4) mərkəz görünür → başlıq və üz həmin zonada.
- Post 1080×1350; highlight 1080×1080, vacib element mərkəzdəki dairədə (diametr ~80%).
- Instagram UI zonası: reels-də alt 320 px və sağ 140 px boş qalır.

## Tipoqrafiya qaydaları
- Maksimum 2 şrift ailəsi, 3 ölçü səviyyəsi. Başlıq 3–7 söz, sətir başına 2–3 söz.
- Sətir aralığı başlıqda 0.95–1.1, hərf aralığı böyük ölçüdə −1…−2%.
- Vurğu sözü rəng və ya kursivlə — ikisi birlikdə yox.
- Bütün Azərbaycan hərfləri yoxlanır (Ə Ğ İ ı Ş Ç Ö Ü).
- HTML-də həmişə `<html lang="az">` — əks halda `text-transform:uppercase` "Mif"-i "MIF" (nöqtəsiz I) yazır.
- Fonu dəyişmək lazımdırsa: yalnız seqmentasiya (`rembg` birefnet-portrait, 720p-də, bir proses bir kadr — yaddaş), üz və geyim toxunulmaz.

## Şablonlar (`templates/ayra/`)
- `editorial.html` — krem fon, kicker + 3 sətir başlıq, kəsilmiş subyekt sağda, blush disk, ad sol sütunda.
- `depth.html` — rəngli fon, böyük açar söz subyektin arxasında, tünd alt panel başlıq + ad.
- `framed.html` — kicker + başlıq yuxarıda, dəyirmi çərçivədə subyekt düz fonda, ad sətri.
- `motion/overlay.html` + `frames.py` — GSAP şəffaf overlay (başlıq kartı, FAKT kartı, söz-söz altyazı, ad lövhəsi), Playwright ilə PNG ardıcıllığı → ffmpeg overlay.
Spec nümunəsi: hər şablonun `{{açar}}`-larını JSON-da ver; `render.py` çatışmayan açarları və kənara 60 px-dən yaxın `data-check` elementlərini bildirir.

## Keyfiyyət
Mətn kənara 64 px-dən yaxın deyil, üz örtülmür, palitradan kənar rəng yoxdur, kadr kəskindir, 270 px-də başlıq oxunur.

## Əməkdaşlıq
`ayra-art-director` → bu → `ayra-design-critic`. İkonlar: `ikon-kitabxana`. Material: `dizayn-resurslari`.
