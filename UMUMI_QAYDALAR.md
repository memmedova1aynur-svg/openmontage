# Ümumi qaydalar (bütün müştərilər)

Bu fayl **bütün müştərilər** üçün ortaq standartlardır. Müştəri profillərində (`templates/expert-reels/experts/`, `instagram-clients/`) təkrarlanmır;
müştəriyə məxsus istisna varsa yalnız profildə, bu fayla istinadla yazılır.

## Görüntü keyfiyyəti — Adaptive Crystal Clear Natural Look

**Məqsəd:** sanki eyni görüntü daha keyfiyyətli kamera və obyektivlə çəkilib — təmiz, kristal aydın, təravətli, təbii və premium; korreksiya nəzərə çarpmasın.

**Vizual referans (təsdiqlənib 2026-11-25):** `montaj/references/crystal_clear_v3/` (`reference_original.jpg` → `reference_v3.jpg`, `params.json`).
V3-ün real parametrləri orada qeyd olunub; onlar yalnız həmin kadr üçün seçilib və **heç bir videoya mexaniki tətbiq olunmur**.

**İş üsulu (standart, rəng təsdiqi soruşulmur, V1/V2/V3 alternativləri hazırlanmır):**
1. Montajdan əvvəl təmsilçi kadrlar analiz olunur (işıq, ağ balansı, dəri tonu, canlılıq, kontrast, kəskinlik, səs-küy).
2. Yalnız ehtiyac olan parametr V3 səviyyəsinə qədər tənzimlənir; yaxşı vəziyyətdə olana toxunulmur; mənbə artıq yüksək keyfiyyətlidirsə korreksiya yoxdur.
3. Tam renderdən əvvəl nümunə kadrlarda yoxlanılır; yalnız problem varsa həmin parametr azalır.
4. Eyni işıq və məkan üçün parametrlər təkrar istifadə oluna bilər (keş), hər videoda uyğunluq yenə yoxlanır.
5. Yekun renderdən sonra texniki yoxlama: kadrlar arası işıq/rəng sıçrayışı, rəng sürüşməsi, kəskinlik (`python -m montaj.crystal check <orijinal> <nəticə>`).

**Alət:** `montaj/crystal.py` (montaj sisteminə qoşulub: plan `"look"` standartı `CRYSTAL`; `templates/expert-reels/pro/talk.py`, `editorial.py`, `build.py`).
CLI: `python -m montaj.crystal analyze <video>` · `sample <video> --start S --dur D --out x.mp4` (hərəkətli nümunə + yoxlama).

**Qadağalar:** qırmızılıq, sarılıq, göyümtüllük, solğunluq · dəri tonunun və üz cizgilərinin dəyişməsi · süni kəskinlik, plastik dəri, HDR effekti ·
rəng temperaturuna səbəbsiz müdaxilə · süni detal, upscaling, ağır AI emalı · kadrlar arası rəng/işıq sıçrayışı · orijinal fonun dəyişməsi.

**Açıq məhdudiyyətlər:** hədlər 3 çəkiliş mühitindən (Xəyyam) kalibrlənib — yeni müştəridə ilk videonun nümunə kadrı yoxlanılmalıdır; HDR mənbədə avtomatik korreksiya yoxdur;
çəkilişdə pozulmuş ağ balans avtomatik düzəldilmir, yalnız xəbərdarlıq verilir; mənbədə olmayan detal yaradılmır.
Üslub presetlərinin öz `color` zənciri (məs. `kinematik`) varsa, o ayrıca yaradıcı qərardır və bu standartı əvəz edir.

**Ləğv edilənlər:** Xəyyam Həsənov üçün C/H/W məcburi filtr seçimləri; "rəng həmişə looks C" qaydası; `looks` əmri ilə variant seçimi (əl ilə müqayisə üçün qalır, standart deyil).
