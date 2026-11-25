# Üslub dəstləri (style kits)

Məqsəd: hər müştəri/video eyni "kart + vurğu qutusu + qutulu altyazı" görünüşündə olmasın. Dəst = ayrı dizayn dili (yazı forması, yer, altyazı,
hərəkət, kart olub-olmaması, musiqi/SFX). Kod: `montaj/kits.py`; yoxlama: `montaj/difference.py`; yaddaş: `montaj/memory.py`.

| Dəst | Nə vaxt | Xüsusiyyət | Məhdudiyyət |
|---|---|---|---|
| classic | təhlükəsiz baza | brend rəngli kartlar, qutulu altyazı | ən tanış; fərqlənmək üçün yox |
| editorial ✅ | psixologiya, ekspert fikri, hekayə | kartsız serif yazı başın üstündə, sola düzlənmiş altyazı | çox yazı sığmır; sakit |
| colorblock ❌ | reklam, təlim, siyahı/addım | yuxarıda tam enli rəng paneli (anda rəng dəyişir), altyazı zolağı | panel yuxarı ~30%-i örtür |
| handnote 👍 | ana-körpə, uşaq, şəxsi məsləhət | əl yazısı (Caveat), altından xətt/dairə/ox/✓, mono altyazı | həddindən artıq olarsa dağınıq |
| kinetic ❌ | reklam, motivasiya, qısa/sürətli | sinema zolaqları, aşağıda bir böyük söz, yuxarıda irəliləyiş xətti | zolaqlar yuxarı 5% və aşağı 24%-i örtür |

**İstifadəçi qərarı (2026-11-25, `montaj/kit_decisions.json`):** editorial yaxşıdır (fon üzərində yazı oxunmurdu; tünd ləkə (scrim) bəyənilmədi, premium deyil → yumşaq üst qradiyent `veil` + Lora serif şrifti), handnote pis deyil; **colorblock və kinetic ümumiyyətlə bəyənilmədi** — təklif olunmur (`variants` onları dayandırır, `--force` yalnız istifadəçi istəsə).
`veil` = kadrın yuxarısında tam enli, çox yumşaq tünd qradiyent (kino başlıqlarındakı kimi, ləkə yox), hər kartsız yazının ALTINDA eyni vaxtda; preflight açılışdakı yazının fon kontrastını ölçür (WCAG <3:1 → veil avtomatik əlavə olunur). Serif başlıqlar: Lora (SIL OFL, Azərbaycan hərfləri tam).

## Seçim qaydası
1. `storyboard` çıxışındakı təklif (son 2 videoda işlənmiş və rədd edilmiş dəstlər xaric) — bir-birindən ən uzaq 3 dəst.
2. Mövzuya/məqsədə görə uyğunluğu yoxla (cədvəl); reklamda hansının daha çox geri dönüş gətirəcəyini səbəbi ilə yaz.
3. Mətn YALNIZ danışıqdan: `content.json` (hook, list, emphasis, claim, words) → `python -m montaj.kits build <dəst> content.json --theme theme.json`.
4. Plan parçasını (`graphics`, `captions`, `sfx`, `zooms`) plana qoş; musiqi sorğusu `music_query` ilə (`music --query`).
5. `variants` fərq və yaddaş yoxlamasından keçməlidir.

## Yeni dəst əlavə etmək
`KITS` lüğətinə metadata (axes!) və `build()`-ə budaq. Yeni qrafika növü lazımdırsa `montaj/editor/graphics.js` + `montaj/graphics.py` (TYPES, DEFAULT_XY).
Hər yeni dəst mövcud dəstlərdən ən azı 4 oxda fərqlənməlidir (test: `test_kit_axes_are_really_different_across_kits`).
