# Caption & Typography Roles — Azərbaycan dili üçün peşəkar altyazı

Mövcud `typography.md` ölçü/vaxt cədvəllərini verir. Bu skill **rolları**, Azərbaycan hərflərini və qərar qaydalarını əlavə edir.
Texniki icra: `tools/subtitle/reels_captions.py` (piksel-dəqiq ASS, Instagram safe zone, `lib/az_text`), `montaj/fonts.py`
(Montserrat, latin + latin-ext → ə ğ ı ö ü ş ç), plan `captions`, `graphics`, `fx`.

## 4 ayrı tipoqrafik rol (hər biri fərqli görünür)
| Rol | Funksiya | Şrift/çəki | Ölçü (1080×1920) | Yer | Müddət/animasiya |
|---|---|---|---|---|---|
| **Altyazı** | danışığın oxunması | Montserrat 600–700, ağ, nazik kontur və ya yarımşəffaf zolaq | ~54–62 px, 1–2 sətir | aşağı-mərkəz, safe zone daxilində (≈ y 0.62–0.78; üzü örtmür) | söz vaxtı ilə; yumşaq giriş, "pop" yox |
| **Hook mətni** | ilk saniyələrdə sual/vəd | Montserrat 800, böyük, az söz (≤ 6) | ~90–120 px | kadrın yuxarı üçdə biri və ya insanın arxası (`fx behind`) | 1.5–3 s; sözlərlə sinxron |
| **Vurğu** | əsas fikir/rəqəm/açar söz | 700–800, bir sözə/ifadəyə | altyazıdan 1.3–1.6× | altyazı xəttində və ya üstündə | söz deyiləndə, 0.8–1.5 s |
| **CTA** | hərəkətə çağırış | 700, sakit kart/zolaq, brend aksenti | ~60–72 px | aşağı-orta, Reels düymələri (sağ) və caption zonasından (alt) kənar | 2.5–4 s, sonda; məzmun YALNIZ təsdiqlənmiş mənbədən |

Ardıcıllıq qaydası: bir kadrda eyni anda ən çoxu **2 rol** (məs. altyazı + vurğu). Hook altyazı ilə üst-üstə düşmür.

## Qaydalar
1. **Brend rəngi aksentdir:** yalnız vurğu sözü, CTA zolağı, kiçik element. Bütün altyazı brend rəngində olmaz. Görüntü rəngi
   (rəng korreksiyası) ilə brend rəngi qarışdırılmır.
2. **Oxunaqlılıq:** kontrast ≥ 4.5:1 (kontur/zolaq ilə). Sətir hündürlüyü ~1.15–1.25, sətirlər arası boşluq tarazdır.
3. **Bölmə:** məna vahidi ilə böl (bağlayıcı və ədat sətrin sonunda qalmasın: "və", "ki", "də", "ilə"). Sətir 14–22 simvol,
   maks 2 sətir. Qısa sətir üstdə, uzun altda (piramida) deyil — **balanslı iki sətir**.
4. **Oxunma müddəti:** ≈3 söz/s, ən azı 1.2 s (`verify` yoxlayır).
5. **Üz və vacib element:** üzü, əlləri, məhsulu örtmür. `verify layout_check` xəbərdarlığı = dəyişdir.
6. **Safe zone:** yuxarı ~14% (ad/zolaq), aşağı ~22% (caption/CTA), sağ ~12% (düymələr). Mətn bu zonalara düşmür.
7. **Premium görünüş:** az effekt, bir şrift ailəsi, 2–3 çəki; bounce/shake/rəngarəng gradient/emoji-spam YOX.
8. **Eni:** hər mətn bloku kadr enindən ≤ 86% tutur (≥ 7% yan boşluq). Sınaq: 64 px Montserrat 800 BÖYÜK hərflə 26 simvol 1000 px-dən çox yer tutdu (kənara sığmadı) → hook-da ölçünü azalt və ya sətrə böl.
9. **Söz-söz vurğu** yalnız ritm və məzmun dəstəkləyəndə (enerjili reklam); sakit/dərs videoda yox.

## Azərbaycan dili yoxlaması (məcburi)
- Hərflər: `ə Ə ğ Ğ ı I İ i ö Ö ü Ü ş Ş ç Ç` — şrift bunları göstərməlidir (render nümunəsində yoxla, fallback tofu □ yoxdur).
- Böyük hərf: `i → İ`, `ı → I` (`lib.az_text.az_upper`); `str.upper()` ilə BÖYÜK yazma.
- ASR "ə" əvəzinə kirill/oxşar simvol verə bilər (`ә`, `ǝ`) → `lib.az_text` ilə normallaşdır.
- Müştəriyə aid ad/termin: profil `glossary` / `fix-word`; mənanı dəyişən təxmin yox.
- Rəqəmlər: `1 200`, `4,5` (Azərbaycan yazılışı); rəqəm yalnız danışıqda varsa.

## Plan sahəsi (təklif; kod dəyişikliyi sonra təsdiqlə)
```json
"creative": {"typography": {"caption": "calm-stroke", "hook": {"text": "…", "role": "hook"},
             "emphasis": [{"word_id": 17, "role": "emphasis"}], "cta": {"role": "cta", "source": "profile:phone"}}}
```
